#!/bin/bash
#
# start_mock.sh - run the ROS 2 software stack against mock hardware:
# the core software (docker-compose-ros.yml) plus the lightweight simulators in
# mock/ (docker-compose-mock-hardware.yml) that stand in for the Teensy and the
# YDLidar. No physical robot and no Gazebo required. See mock/README.md.
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

FILES="-f docker-compose-ros.yml -f docker-compose-mock-hardware.yml"

case "${1:-up}" in
  up)
    # Warn if the real hardware drivers are up - they'd fight the mocks for topics.
    clash=$(docker ps --format '{{.Names}}' \
      | grep -E '^(ros2_micro_ros_agent|ros2_ydlidar_x4)$' || true)
    if [ -n "$clash" ]; then
      echo "WARNING: real hardware containers are running: $clash"
      echo "They publish the same topics as the mocks. Stop them first with:"
      echo "    $DC -f docker-compose-ros-hardware.yml down"
      echo
    fi

    echo "Starting ROS 2 software stack + mock hardware (first run pulls ros:humble-ros-base)..."
    $DC $FILES up -d
    echo
    $DC $FILES ps
    echo
    echo "Up. Next:"
    echo "  ./ros_bash.sh         # then: ros2 topic list / ros2 topic echo /scan"
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
