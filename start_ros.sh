#!/bin/bash
#
# start_ros.sh - run the ROS 2 software stack HERE (this laptop) against the PHYSICAL
# robot's hardware running on the robot itself. The counterpart to start_mock.sh.
#
# Instead of the mock Teensy/lidar, the real sensors and motors come from the hardware
# drivers (docker-compose-ros-hardware.yml) running ON THE ROBOT (robmo-club-robot.local). The two
# machines discover each other over ROS 2 DDS - they must be on the same LAN and the same
# ROS_DOMAIN_ID (default 0, which nothing here overrides). The laptop then runs the brains:
# slam_toolbox, nav2, diff_drive_controller, the urdf/TF publisher, rosbridge and the MCP
# server (docker-compose-ros.yml), plus the Blender robot model + mesh server
# (docker-compose-model.yml) so the robot renders in Foxglove.
#
# Before this is useful, the robot must be running ITS hardware drivers - and ONLY those,
# not its own software stack, or you get two nav2/slam_toolbox nodes fighting on one DDS
# domain:
#     ssh robot        # the ~/.ssh/config alias for operator@robmo-club-robot.local
#     cd robomo-club-robot && docker compose -f docker-compose-ros-hardware.yml up -d
#
# /!\  This drives the REAL motors: publishing /cmd_vel turns the wheels. Develop against
#      ./start_mock.sh first and always end a motion sequence with a zero Twist.
#
# Usage:
#   ./start_ros.sh [up]    Start the software stack here (detached). Default.
#   ./start_ros.sh down    Stop and remove it.
#   ./start_ros.sh logs    Follow the combined logs.
#
# Override the robot host used for the reachability check / hints (the robot's IP varies by
# network; the mDNS name only resolves from the robot's own LAN - its ROBOMO-ROBOT-5G WiFi):
#   ROBOT_HOST=192.168.8.117 ./start_ros.sh up
#
set -euo pipefail

# Run from the repo root so the compose files and the ./model bind mount resolve.
cd "$(dirname "$0")"

# Prefer Docker Compose v2 ("docker compose"), fall back to v1 ("docker-compose").
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "Error: need Docker Compose ('docker compose' or 'docker-compose')." >&2
  exit 1
fi

FILES="-f docker-compose-ros.yml -f docker-compose-model.yml"
ROBOT_HOST="${ROBOT_HOST:-robmo-club-robot.local}"

case "${1:-up}" in
  up)
    # The mock hardware publishes the same topics (/vel, /scan) as the robot's real drivers -
    # running both means two sources fighting over every sensor/actuator topic. Compose labels
    # every container with the file set that created it, so anything carrying the mock-hardware
    # file is a ./start_mock.sh session - including one a reboot auto-resurrected
    # (restart: unless-stopped), where no start script ever ran to warn.
    project="$(basename "$PWD" | tr '[:upper:]' '[:lower:]')"
    mock_up=$(docker ps --filter "label=com.docker.compose.project=$project" \
      --format '{{.Names}}\t{{.Label "com.docker.compose.project.config_files"}}' \
      | awk -F'\t' '$2 ~ /docker-compose-mock-hardware\.yml/ {print $1}' \
      | tr '\n' ' ')
    if [ -n "$mock_up" ]; then
      echo "ERROR: a mock session (./start_mock.sh) is still up: $mock_up"
      echo "Its fake /vel and /scan would fight the robot's real drivers. Stop it first:"
      echo "    ./start_mock.sh down"
      exit 1
    fi

    # Non-fatal: is the robot reachable? Its hardware drivers must be up for the stack to see
    # /scan and to drive the motors.
    if ping -c1 -W1 "$ROBOT_HOST" >/dev/null 2>&1; then
      echo "Robot $ROBOT_HOST is reachable. Make sure its hardware drivers are up:"
    else
      echo "NOTE: can't reach $ROBOT_HOST right now (set ROBOT_HOST=<ip> if its address changed)."
      echo "The stack will start, but won't see sensors until the robot is up and running:"
    fi
    echo "    ssh $ROBOT_HOST -- 'cd robomo-club-robot && docker compose -f docker-compose-ros-hardware.yml up -d'"
    echo

    echo "Starting ROS 2 software stack here (first run pulls ros:humble-ros-base)..."
    $DC $FILES up -d
    echo
    $DC $FILES ps
    echo
    echo "Up. Next:"
    echo "  ./ros_bash.sh         # then: ros2 topic list / ros2 topic echo /scan"
    echo "  Foxglove: connect to ws://localhost:9090 (Rosbridge), then Layout ->"
    echo "            Import from file -> foxglove_layout.json to see the robot"
    echo "  ./start_ros.sh logs   # follow logs"
    echo "  ./start_ros.sh down   # stop everything"
    ;;
  down | stop)
    echo "Stopping ROS 2 software stack..."
    $DC $FILES down
    ;;
  logs)
    $DC $FILES logs -f
    ;;
  *)
    echo "Usage: $0 [up|down|logs]" >&2
    exit 1
    ;;
esac
