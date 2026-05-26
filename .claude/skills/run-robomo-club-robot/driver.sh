#!/usr/bin/env bash
#
# driver.sh - control the robomo robot stack over ROS 2 from the host.
#
# The host has NO ROS install; every ros2 command runs inside a throwaway container on
# the host network + IPC namespace, so it joins the running stack's DDS graph (domain 0).
# Bring the stack up first from the repo root:  ./start_mock.sh up
#
# Examples:
#   .claude/skills/run-robomo-club-robot/driver.sh topics
#   .claude/skills/run-robomo-club-robot/driver.sh pose
#   .claude/skills/run-robomo-club-robot/driver.sh echo /scan --once
#   .claude/skills/run-robomo-club-robot/driver.sh goto 0 0        # autonomous nav (nav2)
#   .claude/skills/run-robomo-club-robot/driver.sh drive 0.2 0.3 4 # manual teleop, 4 s
set -euo pipefail

# Any ros image works; this one has rclpy + common interfaces + nav2_msgs (for the action).
IMG="${ROS_IMAGE:-frankjoshua/ros2-nav2}"

ros() {  # run a ros2 command inside the container, joined to the running stack
  docker run --rm --network host --ipc host --entrypoint bash "$IMG" \
    -c "source /opt/ros/humble/setup.bash && $*"
}

usage() {
  cat <<'EOF'
usage: driver.sh <command> [args]   (run ./start_mock.sh up first)

  topics                  list topics on the graph
  nodes                   list nodes
  echo <topic> [--once]   print messages on a topic     e.g. echo /scan --once
  pose                    current robot position (/odom)
  scan                    one /scan message (metadata + ranges)
  drive <lin> <ang> [s]   manual teleop: publish /cmd_vel for s seconds (default 3)
                          NOTE: fights nav2 if nav2 is also driving - see SKILL.md gotchas
  stop                    publish a single zero /cmd_vel
  goto <x> <y>            autonomous nav: publish a goal to /goal_pose (map frame), returns now
  nav <x> <y>             autonomous nav via the navigate_to_pose action (waits for the result)
EOF
}

cmd="${1:-help}"; shift || true
case "$cmd" in
  topics) ros "ros2 topic list" ;;
  nodes)  ros "ros2 node list" ;;
  echo)   t="${1:?topic required (e.g. /scan)}"; shift || true; ros "ros2 topic echo $t $*" ;;
  pose)   ros "ros2 topic echo /odom --once --field pose.pose.position" ;;
  scan)   ros "ros2 topic echo /scan --once --field ranges | head -c 400; echo" ;;
  drive)  lin="${1:-0.2}"; ang="${2:-0.0}"; dur="${3:-3}"
          ros "timeout $dur ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
               '{linear: {x: $lin}, angular: {z: $ang}}' >/dev/null 2>&1; echo \"drove ${dur}s at lin=$lin ang=$ang, then stopped\"" ;;
  stop)   ros "ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}'" ;;
  goto)   x="${1:?x required}"; y="${2:?y required}"
          ros "ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped \
               '{header: {frame_id: map}, pose: {position: {x: $x, y: $y}, orientation: {w: 1.0}}}'" ;;
  nav)    x="${1:?x required}"; y="${2:?y required}"
          ros "ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
               '{pose: {header: {frame_id: map}, pose: {position: {x: $x, y: $y}, orientation: {w: 1.0}}}}'" ;;
  *)      usage ;;
esac
