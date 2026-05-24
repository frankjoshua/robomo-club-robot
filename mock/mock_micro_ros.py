#!/usr/bin/env python3
"""
mock_micro_ros.py - stand-in for the Teensy micro-ROS node (ros2_micro_ros_agent).

The real firmware (micro-ros2-teensy-4-encoders-srf04, node "micro_ros"):
  - SUBSCRIBES /cmd_vel  (geometry_msgs/Twist)  -> runs the differential-drive motors
  - PUBLISHES  /vel       (geometry_msgs/Twist)  <- body velocity measured by the encoders

This mock models a *perfect* robot: whatever velocity is commanded on /cmd_vel is
reported straight back on /vel. That closes the loop for diff_drive_controller, which
integrates /vel into /odom (and the odom->base_link TF), so slam_toolbox and nav2
behave as if the robot tracks every command exactly. Nothing is actuated.

The real firmware also packs encoder/RPM debug into the unused Twist fields, but
diff_drive_controller only reads linear.x and angular.z, so the mock fills just those.

Tunable via env vars: CMD_VEL_TOPIC, VEL_TOPIC, VEL_PUBLISH_HZ.
"""
import os

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


def _f(name, default):
    return float(os.environ.get(name, default))


class MockMicroRos(Node):
    def __init__(self):
        super().__init__('mock_micro_ros')

        cmd_topic = os.environ.get('CMD_VEL_TOPIC', 'cmd_vel')
        vel_topic = os.environ.get('VEL_TOPIC', 'vel')
        publish_hz = _f('VEL_PUBLISH_HZ', 50.0)

        # Latest commanded velocity; defaults to stopped until the first /cmd_vel.
        self._cmd = Twist()

        self._sub = self.create_subscription(Twist, cmd_topic, self._on_cmd_vel, 10)
        self._pub = self.create_publisher(Twist, vel_topic, 10)
        self._timer = self.create_timer(1.0 / publish_hz, self._publish_vel)

        self.get_logger().info(
            f"mock_micro_ros up: subscribing '{cmd_topic}', echoing to '{vel_topic}' "
            f"at {publish_hz:g} Hz (perfect velocity tracking)"
        )

    def _on_cmd_vel(self, msg: Twist):
        self._cmd = msg

    def _publish_vel(self):
        # Report the commanded velocity as the measured body velocity.
        vel = Twist()
        vel.linear.x = self._cmd.linear.x
        vel.angular.z = self._cmd.angular.z
        self._pub.publish(vel)


def main():
    rclpy.init()
    node = MockMicroRos()
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
