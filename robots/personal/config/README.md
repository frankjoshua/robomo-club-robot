# Personal runtime configuration

These existing root files remain authoritative because Compose, Ansible and
host scripts consume their current paths. This index avoids maintaining a
second copy of live settings. New personal-specific files can live here when
their consumers are updated deliberately.

| File | Purpose |
| --- | --- |
| [tx2-nav2.yaml](../../../config/tx2-nav2.yaml) | Navigation, footprint and obstacle layers |
| [tx2.urdf](../../../config/tx2.urdf) | Runtime sensor mounting transforms |
| [base-calibration.json](../../../config/base-calibration.json) | 262000 counts/rev, 0.1524 m wheel diameter, 0.350 m effective track, 80 RPM |
| [realsense-obstacles.yaml](../../../config/realsense-obstacles.yaml) | Camera streams, initial reset and filtering |
| [tx2-fastdds.xml](../../../config/tx2-fastdds.xml) | General TX2 Fast DDS interfaces |
| [tx2-fastdds-lan.xml](../../../config/tx2-fastdds-lan.xml) | Micro-ROS agent: loopback + LAN, no Tailscale |
| [tx2-cyclonedds.xml](../../../config/tx2-cyclonedds.xml) | Nav2 Cyclone DDS on eth0 |
| [Dockerfile.cyclone](../../../navigation/Dockerfile.cyclone) | Locally built Nav2 image dependency |

Recorded TX2 `.env` selections (paths are relative to the repository root):

```dotenv
ROBOT_DDS_PROFILE=./config/tx2-fastdds.xml
ROBOT_MICRO_ROS_DDS_PROFILE=./config/tx2-fastdds-lan.xml
ROBOT_NAV_IMAGE=ros2-nav2:cyclone-20260912
ROBOT_NAV_RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROBOT_NAV_DDS_PROFILE=./fastdds_udp_only.xml
```

The last Fast DDS Nav2 profile override is retained for rollback and unused
while Cyclone is selected. The local Nav2 image must exist on the target host.
These are personal robot settings, not a club deployment profile.
