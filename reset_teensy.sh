#!/bin/bash
#
# reset_teensy.sh - Reset the robomo Teensy and reconnect its micro-ROS agent
# with NO physical interaction. Run this ON THE ROBOT (robmo-club-robot).
#
# Why this is needed: the deployed Teensy firmware doesn't re-establish its
# micro-ROS session if the agent restarts, and a Teensy doesn't reset when the
# serial port is reopened. This soft-reboots the chip over USB (teensy_loader_cli
# 134-baud trick), then restarts the agent the instant the device re-enumerates
# so the agent is listening when the firmware's startup (with its ~2 s delay) runs.
#
# Requires: teensy_loader_cli in PATH (built from source for Teensy 4.x soft
# reboot; the Ubuntu 18.04 apt build only soft-reboots Teensy 3.x).
#
set -u
AGENT=ros2_micro_ros_agent
IMG=frankjoshua/ros2-micro-ros-agent

echo "[reset_teensy] stopping agent to free the serial port..."
docker stop "$AGENT" >/dev/null 2>&1 || true
docker rm   "$AGENT" >/dev/null 2>&1 || true

echo "[reset_teensy] soft-rebooting the Teensy over USB (no flash)..."
sudo teensy_loader_cli --mcu=TEENSY40 -s -b -v || echo "[reset_teensy] WARN: soft reboot reported an error"

echo "[reset_teensy] waiting for the Teensy serial device to return..."
back=0; for i in $(seq 1 200); do [ -e /dev/teensy ] && { back=1; break; }; sleep 0.1; done
[ "$back" = 1 ] || { echo "[reset_teensy] ERROR: /dev/teensy did not return (Teensy may be in the bootloader: 'sudo teensy_loader_cli --mcu=TEENSY40 -b' to boot it)"; exit 1; }

echo "[reset_teensy] starting the agent on the fresh device..."
docker run -d --name "$AGENT" --network host --ipc host --pid host \
  --device /dev/teensy:/dev/ttyACM0 --restart unless-stopped \
  --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 \
  "$IMG" >/dev/null

sleep 8
if docker logs --tail 25 "$AGENT" 2>&1 | grep -q client_key; then
  echo "[reset_teensy] SUCCESS: Teensy session established (/vel + /cmd_vel live)."
else
  echo "[reset_teensy] No session yet. Re-run, or check: docker logs $AGENT"
  exit 1
fi
