# Repository scope: two robots

Use [robots/README.md](robots/README.md) to select club or personal records.
Club: Nano / wheelchair base / robmo-club-robot.local / ROBOMO-ROBOT-5G.
Personal: TX2 / 14-inch circular base / tx2.local / josh-robot.
Keep each robot's photos, specs, models and reports under its own robots/ directory.
Shared software and existing runtime config paths remain at the repository root.
Do not apply one robot's calibration, sensor geometry or power wiring to the other.
The notes below concern the personal TX2 only; they do not set a default target.

# Current TX2 hardware facts

- Photo references: `images/personal_robot/` contains Josh's personal TX2 robot.
  The `images/100001585*.jpg` files show the separate club robot (wheelchair
  base and Jetson Nano). Do not mix the two robots' photo references or geometry.

- The personal robot is `tx2.local`; select the task target from context.
- User-confirmed 2026-09-12: all TX2 components fit within the 14-inch round
  base (diameter 0.3556 m). Use that physical envelope, not the other robot's
  0.32 m radius. TX2 runtime configuration: config/tx2-nav2.yaml and config/tx2.urdf.
- User-confirmed 2026-09-12: its Teensy is powered through USB. It has no
  separate power supply. Disconnecting its USB cable removes its power.
- Do not apply the older club/Nano robot's separate Teensy VIN/bus-strip
  wiring description to this TX2. Those are different robots.
- A hub power-control command reporting success does not prove that USB VBUS
  actually switched off. Do not infer a separate supply from a failed USB reset.

# TX2 ROS deployment

- TX2 Compose project names are `ros_hardware` and `ros_software`; pass `-p` when
  recreating services so existing containers are managed by the correct project.
- TX2 `.env` selects `ROBOT_DDS_PROFILE=./config/tx2-fastdds.xml`, isolating ROS
  from club Wi-Fi. Another ROS host was observed publishing duplicate `/scan`
  and `/vel` in domain 0. Preserve the selected profile; see
  robots/personal/docs/tx2-network-isolation.md. Generic/mock deployments keep their own profile.
- Current calibration and validation limits: robots/personal/docs/calibration-2026-09-12.md.

- TX2 Nav2 uses the local ros2-nav2:cyclone-20260912 image and
  ROBOT_NAV_RMW_IMPLEMENTATION=rmw_cyclonedds_cpp. Recipe: navigation/Dockerfile.cyclone.
  config/tx2-cyclonedds.xml selects eth0. Fresh Fast DDS service clients timed out
  against this Nav2; use matching Cyclone clients or docker exec inside ros2_nav.
  driver.sh does this automatically while Nav2 is running. Other services retain
  Fast DDS; topic interoperability passed, cross-vendor RPC did not.
- Preserve robot-ros-network-filter.service (enabled before Docker), which keeps
  the other club robot's wlan0 domain-0 traffic out.
- Laptop ROS2y uses run_tx2.sh and cyclonedds.xml on robot Wi-Fi. Its UFW rule
  allows TX2 192.168.8.230 UDP 7400:8000 on wlp2s0; without it LAN data was blocked.
- Nav2 depth input is /nav/obstacle_points, a fresh 5 Hz relay of the original
  camera cloud. Keep ros2_depth_nav_relay running with navigation.

- TX2 micro-ROS agent uses ROBOT_MICRO_ROS_DDS_PROFILE=./config/tx2-fastdds-lan.xml
  (LAN address 192.168.8.230 plus local loopback; no Tailscale). With the previous multi-interface profile,
  graph visibility worked while ROS2y commands failed delivery. After this
  profile change and agent recreation, actual ROS2y W/X input drove both wheels
  and stopped them. See robots/personal/docs/teleop-diagnostics-2026-09-12.md; retain this override.
