#!/bin/bash
#
# start_mock.sh - run the complete mock: the ROS 2 software stack against mock hardware:
# the core software (docker-compose-ros.yml) plus the lightweight simulators in
# mock/ (docker-compose-mock-hardware.yml) that stand in for the Teensy and the
# YDLidar. No physical robot and no Gazebo required. See mock/README.md.
#
# Also layers docker-compose-model.yml: loads the Blender-built robot model
# (model/robomo.urdf) and serves its meshes over HTTP so the robot is visible in
# Foxglove Studio (connect to ws://localhost:9090). See model/README.md.
#
# Usage:
#   ./start_mock.sh [up]    Start everything (detached). Default.
#   ./start_mock.sh down    Stop and remove everything.
#   ./start_mock.sh logs    Follow the combined logs.
#
set -euo pipefail

# Run from the repo root so the compose files and the ./mock bind mount resolve.
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

FILES="-f docker-compose-ros.yml -f docker-compose-mock-hardware.yml -f docker-compose-model.yml"

case "${1:-up}" in
  up)
    # The robot's real drivers publish the same topics (/vel, /scan) as the mocks - refuse
    # to mix a real-robot session in. Compose labels every container with the file set that
    # created it: created with the ros (or local ros-hardware) files but WITHOUT the
    # mock-hardware file means a ./start_ros.sh session or local hardware drivers. The label
    # survives a reboot's auto-resurrection (restart: unless-stopped), where no start script
    # ever ran to warn.
    project="$(basename "$PWD" | tr '[:upper:]' '[:lower:]')"
    real_up=$(docker ps --filter "label=com.docker.compose.project=$project" \
      --format '{{.Names}}\t{{.Label "com.docker.compose.project.config_files"}}' \
      | awk -F'\t' '$2 ~ /docker-compose-ros(-hardware)?\.yml/ && $2 !~ /docker-compose-mock-hardware\.yml/ {print $1}' \
      | tr '\n' ' ')
    if [ -n "$real_up" ]; then
      echo "ERROR: a real-robot session is still up: $real_up"
      echo "The robot's real drivers publish the same topics (/vel, /scan) as the mocks. Stop it first:"
      echo "    ./start_ros.sh down"
      echo "    $DC -f docker-compose-ros-hardware.yml down   # if the hardware drivers run here"
      exit 1
    fi

    echo "Starting ROS 2 software stack + mock hardware (first run pulls ros:humble-ros-base)..."
    $DC $FILES up -d
    echo
    $DC $FILES ps
    echo
    echo "Up. Next:"
    echo "  ./ros_bash.sh         # then: ros2 topic list / ros2 topic echo /scan"
    echo "  Foxglove: connect to ws://localhost:9090, add a 3D panel,"
    echo "            then Custom layers -> URDF -> /robot_description to see the robot"
    echo "  ./start_mock.sh logs  # follow logs"
    echo "  ./start_mock.sh down  # stop everything"
    ;;
  down | stop)
    echo "Stopping ROS 2 software stack + mock hardware..."
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
