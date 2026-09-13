# TX2 ROS traffic isolation

On 2026-09-12, another ROS host appeared on the shared club network with the same
`ydlidar_ros2_driver_node` and `micro_ros` names. The TX2 graph then had two `/scan`
publishers and two `/vel` publishers. Real TX2 scans had 1290 ranges at about
3.9 Hz; the other source had 650 ranges at about 9 Hz. The mixed `/scan` stream
and competing measured velocities invalidate mapping and odometry. The affected
`return-refined-1` calibration record is rejected, not resampled into a result.

`config/tx2-fastdds.xml` limits DDS to loopback, the dedicated robot LAN
(192.168.8.230), and the TX2 Tailscale address (100.96.218.61). It excludes the
TX2's club Wi-Fi interface, wlan0 (10.42.30.213 during this session). Both the
robot and a fresh ROS2y-container listener then saw exactly one source for
`/scan`, `/vel`, `/odom`, `/joint_states`, and `/base/config`.

The TX2's repository `.env` contains:

```
ROBOT_DDS_PROFILE=./config/tx2-fastdds.xml
```

Hardware and most software services select that profile through `${ROBOT_DDS_PROFILE:-./fastdds_udp_only.xml}`. Nav2 now has the exception described below.
The driver uses a running Nav2 container for ordinary ROS commands, and reads the
DDS profile from `.env` without executing it when using a throwaway container.
Generic/mock deployments retain their original UDP profile unless configured.
The profile uses this TX2's addresses; update it if the robot LAN or Tailscale
address changes. ROS_DOMAIN_ID and Teensy firmware were not changed. This is
network-interface isolation, not a security/authentication boundary.

Use the existing Compose project names when recreating services:

```
docker compose -p ros_hardware -f docker-compose-ros-hardware.yml ...
docker compose -p ros_software -f docker-compose-ros.yml ...
```

`diagnostics/check_unique_sources.py` verifies graph publisher counts and scan
layout from a fresh listener. `ros_sources` now appears in `/diagnostics`, with
ERROR for duplicate critical publishers. Calibration refuses to start or
continues only while each critical topic has one publisher. The isolated runner
test injects a second velocity publisher and verifies a stopped result.

References: [Fast DDS interface whitelist](https://fast-dds.docs.eprosima.com/en/v2.14.7/fastdds/transport/whitelist.html).
A separate ROS domain for each robot is another option, but the micro-ROS client
must use that domain too; merely setting the agent environment is not generally
a firmware-domain override.

## Navigation restart repair later on September 12

After the full restart, Nav2 had fresh upstream sensors but stale observation
buffers, intermittent graph visibility, and a UDP receive queue near 16 MiB.
The interface-whitelisted Nav2 transport repeatedly backed up. A trial using only
the robot LAN address failed to receive the local odometry transform. Returning
Nav2 to normal wildcard UDP receive sockets temporarily drained the queue, but
stale inputs returned under sustained checks; this did not complete the repair. The exact Fast DDS internal fault has not been established.

TX2 `.env` now also contains:

```
ROBOT_NAV_DDS_PROFILE=./fastdds_udp_only.xml
ROBOT_NAV_IMAGE=ros2-nav2:cyclone-20260912
ROBOT_NAV_RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Nav2 uses Cyclone DDS on eth0 via config/tx2-cyclonedds.xml. Its Fast DDS profile
override remains available for rollback but is unused with Cyclone. Build the
local image with `docker build -t ros2-nav2:cyclone-20260912 -f navigation/Dockerfile.cyclone .`.
Other services retain the restricted Fast DDS TX2 profile. Matching Cyclone
service/action clients are required for Nav2; ordinary sensor topics interoperate.
Generic deployments fall back to ROBOT_DDS_PROFILE, then fastdds_udp_only.xml.

To retain separation from other club robots, `robot-ros-network-filter.service`
installs an INPUT rule dropping IPv4 UDP destination ports 7400–8000 on wlan0.
The service is enabled and ordered before Docker at boot. It does not filter the
robot LAN or Tailscale interfaces, or SSH/browser ports. This range covers this
stack's domain-0 DDS ports; revisit it if changing domains or participant counts.
The script checks for its exact tagged rule before adding it and never flushes
other firewall rules. Sources are in ansible/files/robot-ros-network-filter and
the adjacent .service file; installed paths are /usr/local/sbin and
/etc/systemd/system respectively. They were installed directly on the TX2.

Camera viewer buffering and repeated depth-cloud processing were also bounded;
see [navigation-restart-2026-09-12.md](navigation-restart-2026-09-12.md). Reducing
those loads alone did not fix the stale Nav2 buffers, so do not describe them as
the complete transport fix.

The laptop ROS2y client uses the sibling repository's run_tx2.sh and
cyclonedds.xml on 192.168.8.0/24. Its UFW now permits UDP 7400:8000 specifically
from 192.168.8.230 on wlp2s0. Direct robot-LAN traffic had previously been blocked;
self-check passed after this rule. Update addresses/interfaces when changing LANs.

The TX2 router's Wi-Fi SSID is `josh-robot`. `ROBOMO-ROBOT-5G` is a different
router despite also using 192.168.8.0/24; switching there broke direct TX2 access.
The ROS2y Cyclone peer list includes both 127.0.0.1 and 192.168.8.230 so fresh
local diagnostic participants discover the open interface as well as the robot.

The micro-ROS agent now has a separate TX2 override:
`ROBOT_MICRO_ROS_DDS_PROFILE=./config/tx2-fastdds-lan.xml`. It advertises the
LAN address, 192.168.8.230, plus local loopback. Actual ROS2y teleop delivery and both wheel responses
were verified after selecting this profile and recreating the agent. Direct
native DDS access to this agent over Tailscale is no longer provided by this
profile; TX2-local consumers and the LAN ROS2y client are the verified paths.
See teleop-diagnostics-2026-09-12.md for the controlled comparison.
