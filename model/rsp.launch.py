"""robot_state_publisher for the Blender-built URDF.

Wraps robot_description in ParameterValue(value_type=str) so the colons in the http:// mesh
URL aren't misparsed as YAML. The stock robot_description launch.py omits this wrap and dies
with "Unable to parse the value of parameter robot_description as yaml" on any URDF whose text
contains a colon (e.g. an http mesh URL). Bind-mounted by docker-compose-model.yml.

The URDF (model/robomo.urdf) is plain XML with all-fixed joints, so we read it directly
(no xacro) and run only robot_state_publisher (no joint_state_publisher needed for fixed
joints). That keeps the only dependency robot_state_publisher, which ships in every Humble
image - so this runs on ros:humble-ros-base and joins the same DDS domain as the rest of the
stack. (It must: the dedicated frankjoshua/ros2-urdf image is built on Jazzy, whose Fast DDS
wire format is incompatible with the Humble stack and corrupts discovery for every node.)
"""
import os

from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    urdf = os.environ.get("ROBOMO_URDF", "/model/robomo.urdf")
    with open(urdf) as f:
        robot_description = ParameterValue(f.read(), value_type=str)
    return LaunchDescription([
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),
    ])
