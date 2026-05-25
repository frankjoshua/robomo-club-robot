#!/usr/bin/env python3
"""
mock_ydlidar.py - stand-in for the YDLidar X4 driver (ros2_ydlidar_x4).

Publishes a sensor_msgs/LaserScan on /scan at 10 Hz: the view a 360 deg lidar gets
inside a rectangular room that contains obstacles (boxes and round pillars). For each
beam it returns the distance to the nearest surface - outer wall or obstacle - so
obstacles correctly occlude what's behind them. It also publishes the
base_link -> laser_frame static transform, like the real driver's launch file.

World-locking (default on): the mock subscribes to /odom (from diff_drive_controller)
and re-projects the room+obstacles from the robot's current pose every scan, so walls
and obstacles sweep past correctly as the robot drives - enough for slam_toolbox to
build a real map and for nav2 to plan around the obstacles. The scene is fixed in the
odom frame, centred on the odom origin (where the robot starts). With no /odom (running
the mock alone) the robot stays at the origin and the scene is fixed. Set
WORLD_LOCKED=false to force that even when /odom is present.

Surfaces beyond range_max read as +inf, like a real lidar, so the robot reveals more of
a large room as it explores. Still a toy: 2D, no noise, static obstacles - not a
substitute for a real simulator.

Matches the real driver's contract:
  topic     /scan        (sensor_msgs/LaserScan)
  frame_id  laser_frame
  angles    -pi .. +pi   (full 360 deg, like the driver's -180..180 config)
  range     0.12 .. 12.0 m

Tunable via env vars: SCAN_TOPIC, LASER_FRAME, BASE_FRAME, ODOM_TOPIC, WORLD_LOCKED,
SCAN_HZ, SCAN_SAMPLES, RANGE_MIN, RANGE_MAX, ROOM_WIDTH, ROOM_LENGTH, OBSTACLES,
PUBLISH_LASER_TF.

OBSTACLES is a JSON list (metres, odom frame); each item is
  ["box", center_x, center_y, width, height]   or   ["circle", center_x, center_y, radius]
Defaults to a built-in furnished-room layout (keeps the origin and through-paths clear).
"""
import json
import math
import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster

# Default obstacles for a ~20x16 m room. Boxes are [cx, cy, w, h]; pillars [cx, cy, r].
# Laid out to leave the origin (robot start) and paths between them clear.
DEFAULT_OBSTACLES = [
    ["box", 5.0, 4.0, 2.0, 2.0],     # furniture block
    ["box", -6.0, 3.5, 3.0, 1.0],    # long table
    ["box", 4.5, -5.0, 1.5, 3.0],    # cabinet
    ["box", -5.0, -4.5, 2.0, 2.0],   # block
    ["box", 0.0, 6.0, 5.0, 0.4],     # partial divider wall (gaps at the room sides)
    ["circle", 3.0, -1.5, 0.5],      # pillar
    ["circle", -3.0, 1.5, 0.5],      # pillar
    ["circle", -2.0, -6.0, 0.6],     # pillar
]


def _f(name, default):
    return float(os.environ.get(name, default))


def _b(name, default):
    return os.environ.get(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


class MockYdlidar(Node):
    def __init__(self):
        super().__init__('mock_ydlidar')

        scan_topic = os.environ.get('SCAN_TOPIC', 'scan')
        odom_topic = os.environ.get('ODOM_TOPIC', 'odom')
        self._frame_id = os.environ.get('LASER_FRAME', 'laser_frame')
        self._base_frame = os.environ.get('BASE_FRAME', 'base_link')
        self._world_locked = _b('WORLD_LOCKED', True)
        rate_hz = _f('SCAN_HZ', 10.0)
        self._num_readings = int(_f('SCAN_SAMPLES', 720))  # 0.5 deg resolution
        self._range_min = _f('RANGE_MIN', 0.12)
        self._range_max = _f('RANGE_MAX', 12.0)

        # Room half-extents, centred on the odom origin (metres).
        self._room_hx = _f('ROOM_WIDTH', 20.0) / 2.0
        self._room_hy = _f('ROOM_LENGTH', 16.0) / 2.0

        # Obstacles: JSON env override, else the built-in layout.
        raw = os.environ.get('OBSTACLES')
        try:
            obstacles = json.loads(raw) if raw else DEFAULT_OBSTACLES
        except (ValueError, TypeError):
            self.get_logger().warn('OBSTACLES is not valid JSON; using the default layout')
            obstacles = DEFAULT_OBSTACLES
        self._boxes = []    # (xmin, xmax, ymin, ymax)
        self._circles = []  # (cx, cy, r)
        for o in obstacles:
            if o[0] == 'box':
                cx, cy, w, h = o[1], o[2], o[3], o[4]
                self._boxes.append((cx - w / 2.0, cx + w / 2.0, cy - h / 2.0, cy + h / 2.0))
            elif o[0] == 'circle':
                self._circles.append((o[1], o[2], o[3]))

        self._angle_min = -math.pi
        self._angle_max = math.pi
        self._angle_increment = (self._angle_max - self._angle_min) / self._num_readings
        self._scan_time = 1.0 / rate_hz
        self._time_increment = self._scan_time / self._num_readings
        self._beam_angles = [self._angle_min + i * self._angle_increment
                             for i in range(self._num_readings)]

        # Robot pose in the odom frame; (0, 0, 0) until the first /odom.
        self._px = 0.0
        self._py = 0.0
        self._yaw = 0.0

        self._pub = self.create_publisher(LaserScan, scan_topic, 10)
        if self._world_locked:
            self._odom_sub = self.create_subscription(Odometry, odom_topic, self._on_odom, 10)
        self._timer = self.create_timer(1.0 / rate_hz, self._publish_scan)

        if _b('PUBLISH_LASER_TF', True):
            self._publish_static_tf()

        mode = f"world-locked (following '{odom_topic}')" if self._world_locked else "fixed scene"
        self.get_logger().info(
            f"mock_ydlidar up: publishing '{scan_topic}' (frame '{self._frame_id}') at "
            f"{rate_hz:g} Hz - {2 * self._room_hx:g}x{2 * self._room_hy:g} m room, "
            f"{len(self._boxes)} boxes + {len(self._circles)} pillars, "
            f"{self._num_readings} samples, {mode}"
        )

    def _on_odom(self, msg: Odometry):
        self._px = msg.pose.pose.position.x
        self._py = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        # Yaw from quaternion (planar robot).
        self._yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                               1.0 - 2.0 * (q.y * q.y + q.z * q.z))

    @staticmethod
    def _ray_aabb(px, py, dx, dy, xmin, xmax, ymin, ymax):
        """Distance from (px,py) along unit (dx,dy) to an axis-aligned box (slab method).
        Returns the exit distance when the origin is inside the box (the room) or the entry
        distance when outside (an obstacle); math.inf if the ray misses or it's behind."""
        tmin, tmax = -math.inf, math.inf
        for p, d, lo, hi in ((px, dx, xmin, xmax), (py, dy, ymin, ymax)):
            if abs(d) < 1e-12:
                if p < lo or p > hi:
                    return math.inf
            else:
                t1 = (lo - p) / d
                t2 = (hi - p) / d
                if t1 > t2:
                    t1, t2 = t2, t1
                if t1 > tmin:
                    tmin = t1
                if t2 < tmax:
                    tmax = t2
        if tmax < tmin or tmax < 0.0:
            return math.inf
        return tmax if tmin < 0.0 else tmin

    @staticmethod
    def _ray_circle(px, py, dx, dy, cx, cy, r):
        """Distance from (px,py) along unit (dx,dy) to a circle; math.inf if no hit ahead."""
        fx, fy = px - cx, py - cy
        b = 2.0 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - r * r
        disc = b * b - 4.0 * c
        if disc < 0.0:
            return math.inf
        s = math.sqrt(disc)
        t1 = (-b - s) / 2.0
        if t1 > 1e-9:
            return t1
        t2 = (-b + s) / 2.0
        return t2 if t2 > 1e-9 else math.inf

    def _ray_scene(self, phi):
        """Nearest surface (outer wall or any obstacle) along world heading phi."""
        dx, dy = math.cos(phi), math.sin(phi)
        # Outer walls: robot is inside the room, so this returns the exit (wall) distance.
        best = self._ray_aabb(self._px, self._py, dx, dy,
                              -self._room_hx, self._room_hx, -self._room_hy, self._room_hy)
        for xmin, xmax, ymin, ymax in self._boxes:
            d = self._ray_aabb(self._px, self._py, dx, dy, xmin, xmax, ymin, ymax)
            if d < best:
                best = d
        for cx, cy, r in self._circles:
            d = self._ray_circle(self._px, self._py, dx, dy, cx, cy, r)
            if d < best:
                best = d
        return best if self._range_min <= best <= self._range_max else math.inf

    def _compute_ranges(self):
        return [self._ray_scene(self._yaw + a) for a in self._beam_angles]

    def _publish_scan(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.angle_min = self._angle_min
        msg.angle_max = self._angle_max
        msg.angle_increment = self._angle_increment
        msg.time_increment = self._time_increment
        msg.scan_time = self._scan_time
        msg.range_min = self._range_min
        msg.range_max = self._range_max
        msg.ranges = self._compute_ranges()
        self._pub.publish(msg)

    def _publish_static_tf(self):
        # Latched (transient-local) so late subscribers still receive it.
        self._static_br = StaticTransformBroadcaster(self)
        tf = TransformStamped()
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.header.frame_id = self._base_frame
        tf.child_frame_id = self._frame_id
        tf.transform.translation.z = 0.02  # matches the real launch's "0 0 0.02"
        tf.transform.rotation.w = 1.0       # identity rotation
        self._static_br.sendTransform(tf)
        self.get_logger().info(f"published static TF {self._base_frame} -> {self._frame_id}")


def main():
    rclpy.init()
    node = MockYdlidar()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
