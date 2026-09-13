# TX2 low obstacle coverage

The owner reported contact with office-chair casters on 2026-09-12. The original
full-height depth voxel layer ignored points below 5 cm and used 12.5 cm vertical
cells starting at floor height. Its bottom cell therefore combined floor and low
obstacles. Finer vertical cells reduce the risk of clearing an obstacle with
a ray through nearby free space. The confirmed old/new test difference is that
the old settings did not mark the 3.5 cm obstacle; they did mark the 7 cm one.

`config/tx2-nav2.yaml` adds `low_obstacle_layer` to both costmaps, retaining the
existing full-height layer. The additional layer marks heights 2.5–60 cm and
uses 4 cm vertical cells, with origin -2.5 cm and 16 cells. Its 61.5 cm upper
boundary includes the measured camera origin (39.8 cm). It clears using full
depth rays and combines by maximum cost, independently of the high lidar plane.
The 14-inch footprint and navigation speed settings are unchanged.

A network-isolated Humble Nav2 test publishes floor, 3.5 cm and 7 cm obstacles,
then rays passing above those obstacles, then rays directly through their former
cells. Both new costmaps report free floor, mark both obstacles, retain them under
higher clearing rays, and clear them when the occupied volume is observed free.
Fixture: `diagnostics/check_low_obstacles_isolated.py`. Run only in network-none
Docker, ROS_DOMAIN_ID=88, ROS_LOCALHOST_ONLY=1; it publishes synthetic sensors and
TF and must never share the live robot's graph.

The calibration runner also retains observed low points in odom for the duration
of each bounded run. This prevents a previously visible caster disappearing from
its proximity check as it leaves the forward camera view. It deliberately retains
moving low objects until that run ends, which can cause a conservative stop.
An isolated test verifies this stop after the current cloud no longer contains
the object (`test_laser_motion_guard_isolated.py`).

These changes improve handling of observed low obstacles. They do not provide
360-degree low-obstacle sensing. A chair wheel beside/behind the camera, or one
never visible to it, remains a physical sensing limitation. Do not change the
camera transform to pretend the camera is tilted: a mounting change requires
physical adjustment and a new floor-plane measurement.

Nav2 now consumes `/nav/obstacle_points` from `depth_nav_relay.py` at up to 5 Hz,
matching the local costmap update frequency. The camera's original 15 Hz cloud
remains available. The relay forwards serialized clouds without changing points,
frames, or timestamps, retains only the newest sample, and stops output when no
fresh input arrives. The isolated layer fixture publishes to this Nav2 input;
a separate isolated relay test checks exact payload/timestamp preservation and
absence of stale replay.
