"""robot_state_publisher for the Blender-built URDF.

Wraps robot_description in ParameterValue(value_type=str) so the colons in the http:// mesh
URL aren't misparsed as YAML. The stock robot_description launch.py omits this wrap and dies
with "Unable to parse the value of parameter robot_description as yaml" on any URDF whose text
contains a colon (e.g. an http mesh URL). Bind-mounted by docker-compose-model.yml.
"""
import os

from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    urdf = os.environ.get("ROBOMO_URDF", "/model/robomo.urdf")
    robot_description = ParameterValue(Command(["xacro ", urdf]), value_type=str)
    return LaunchDescription([
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            name="joint_state_publisher",
            output="screen",
        ),
    ])
