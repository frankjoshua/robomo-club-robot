#!/usr/bin/env python3
"""
mock_ydlidar.py - stand-in for the YDLidar X4 driver (ros2_ydlidar_x4).

Publishes a sensor_msgs/LaserScan on /scan at 10 Hz: the view a 360 deg lidar gets
inside an empty rectangular room (a "box"). It also publishes the
base_link -> laser_frame static transform, exactly like the real driver's launch
file, so /scan is usable by slam_toolbox even when the urdf container isn't running.

World-locking (default on): the mock subscribes to /odom (published by
diff_drive_controller) and re-projects the box from the robot's current pose every
scan, so the walls move past correctly as the robot drives. That makes slam_toolbox
actually build a map and nav2 actually navigate. The box is fixed in the odom frame,
centred on the odom origin (where the robot starts). With no /odom available (running
the mock on its own) the robot stays at the origin and you get a fixed centred box -
handy for a pure plumbing check. Set WORLD_LOCKED=false to force that fixed box even
when /odom is present.

This is still a toy: walls only, no noise, no dynamic obstacles, and it assumes the
robot stays inside the box (drive outside and beams that miss read as out-of-range).
It is not a substitute for a real simulator.

Matches the real driver's contract:
  topic     /scan        (sensor_msgs/LaserScan)
  frame_id  laser_frame
  angles    -pi .. +pi   (full 360 deg, like the driver's -180..180 config)
  range     0.12 .. 12.0 m

Tunable via env vars: SCAN_TOPIC, LASER_FRAME, BASE_FRAME, ODOM_TOPIC, WORLD_LOCKED,
SCAN_HZ, SCAN_SAMPLES, RANGE_MIN, RANGE_MAX, BOX_WIDTH, BOX_LENGTH, PUBLISH_LASER_TF.
"""
import math
import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster


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

        # Half-extents of the room, centred on the odom origin (metres).
        self._half_x = _f('BOX_WIDTH', 4.0) / 2.0
        self._half_y = _f('BOX_LENGTH', 4.0) / 2.0

        self._angle_min = -math.pi
        self._angle_max = math.pi
        self._angle_increment = (self._angle_max - self._angle_min) / self._num_readings
        self._scan_time = 1.0 / rate_hz
        self._time_increment = self._scan_time / self._num_readings
        self._beam_angles = [self._angle_min + i * self._angle_increment
                             for i in range(self._num_readings)]

        # Robot pose in the odom frame; (0, 0, 0) until the first /odom (or always,
        # when not world-locked) -> a fixed box centred on the robot.
        self._px = 0.0
        self._py = 0.0
        self._yaw = 0.0

        self._pub = self.create_publisher(LaserScan, scan_topic, 10)
        if self._world_locked:
            self._odom_sub = self.create_subscription(Odometry, odom_topic, self._on_odom, 10)
        self._timer = self.create_timer(1.0 / rate_hz, self._publish_scan)

        if _b('PUBLISH_LASER_TF', True):
            self._publish_static_tf()

        mode = f"world-locked (following '{odom_topic}')" if self._world_locked else "fixed box"
        self.get_logger().info(
            f"mock_ydlidar up: publishing '{scan_topic}' (frame '{self._frame_id}') at "
            f"{rate_hz:g} Hz - {2 * self._half_x:g}x{2 * self._half_y:g} m box room, "
            f"{self._num_readings} samples, {mode}"
        )

    def _on_odom(self, msg: Odometry):
        self._px = msg.pose.pose.position.x
        self._py = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        # Yaw from quaternion (planar robot).
        self._yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                               1.0 - 2.0 * (q.y * q.y + q.z * q.z))

    def _ray_box_range(self, phi):
        """Distance from the robot to the nearest box wall along world heading phi."""
        dx, dy = math.cos(phi), math.sin(phi)
        best = math.inf
        if abs(dx) > 1e-9:
            for wall_x in (self._half_x, -self._half_x):
                t = (wall_x - self._px) / dx
                if 0.0 < t < best:
                    y = self._py + t * dy
                    if -self._half_y - 1e-6 <= y <= self._half_y + 1e-6:
                        best = t
        if abs(dy) > 1e-9:
            for wall_y in (self._half_y, -self._half_y):
                t = (wall_y - self._py) / dy
                if 0.0 < t < best:
                    x = self._px + t * dx
                    if -self._half_x - 1e-6 <= x <= self._half_x + 1e-6:
                        best = t
        return best if self._range_min <= best <= self._range_max else math.inf

    def _compute_ranges(self):
        return [self._ray_box_range(self._yaw + a) for a in self._beam_angles]

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
