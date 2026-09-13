# TX2 wheel and gyro odometry calibration — 2026-09-11

This is the September 11 baseline. The [September 12 refinement](calibration-2026-09-12.md)
contains the current saved values and remaining validation.

The robot lost its map during turns. Raw laser registration independently confirmed
that wheel odometry overstated distance by about 2.3 times. During reversals the
encoders sometimes reported rotation while the laser and RealSense gyro measured
little body rotation. That transient cannot be fixed by a constant wheel-track value.
Its mechanical cause (caster resistance, tire slip, drivetrain play, etc.) is not proven.

## Saved calibration

| Parameter | Before | After |
|---|---:|---:|
| Effective counts per wheel revolution | 130000 | 310000 |
| Wheel diameter | 0.150 m | 0.1524 m |
| Effective track | 0.350 m | 0.300 m |
| Maximum RPM setting | 80 | 80 |
| Lidar position in base_link | (0.030, 0, 1.23) m | (0.105, 0.015, 1.23) m |

The diameter comes from the owner's [Zagros base specification](https://www.zagrosrobotics.com/shop/item.aspx?itemid=688).
Counts and track are **effective rolling estimates**, not a shaft-revolution count
or a ruler measurement. The motor and encoder variant is unverified. The 80 RPM
setting is retained and does not establish the achievable loaded speed.

The new distance conversion is 0.42606 times the old conversion. Steady turns
suggested roughly 0.5 times the old angular conversion, which gives the 0.30 m
effective track. Gyro heading handles the variable reversal behavior. Three turns
independently estimated lidar X offsets of 0.100–0.108 m; the previous 0.030 m
offset caused several centimetres of apparent translation during rotation.

`config/base-calibration.json` is applied through:

```bash
.claude/skills/run-robomo-club-robot/driver.sh calibrate-base
```

This requires stopped wheels and no active `/cmd_vel` controller, writes via
`/base/set_geometry`, and verifies `/base/config` readback. Firmware saves the
values in EEPROM, so no boot-time publisher or firmware flash is needed. The
firmware's existing first-boot defaults are different; use this file after replacing
or erasing the Teensy. Encoder wiring/signs and PID gains were preserved.

## Odometry implementation

`ros2_diff_drive_controller` runs the bind-mounted `odometry/wheel_imu_odometry.py`
using its existing Humble image. It integrates calibrated wheel translation and
the D435i angular rate transformed from its optical frame to `base_link`.
This is planar gyro-assisted integration, not an EKF and not camera visual odometry.
It does not integrate accelerometer acceleration into position.

The node learns gyro bias from stationary samples, freezes heading after a second
of stationary wheel feedback, publishes `/odom` and `odom -> base_link` at 50 Hz,
and reports `odometry` status in `/diagnostics`. Old camera timestamps are rejected.
If gyro data is missing or its bias is not ready, it uses wheel heading with a WARN.
If wheel feedback is stale for 0.25 s, integration stops and status becomes ERROR.
Fallback does not cure wheel slip; check diagnostics before investigating another map failure.
Covariances are engineering estimates, not filter-derived uncertainty.

Mock Compose explicitly disables IMU use. No extra gyro requirement is imposed on mocks.

## Measurement method and evidence

Navigation was stopped during all raw motor tests. `driver.sh laser-check` runs
15% motor power for at most 2.5 s, checks fresh lidar/depth/wheel/odom data and
clearance, aborts on another controller's commands, and repeatedly publishes zero
at the end. Every executed test reported stopped wheels afterward.
The clearance check uses the swept circular footprint with 8 cm extra padding;
points beside the path are not treated as head-on obstacles. Before motion it now
waits for at least six stationary scans, since DDS discovery can consume the
initial fixed waiting period.

`diagnostics/compare_laser_motion.py` registers stationary endpoint laser scans
directly, using point-to-line ICP. It does not use SLAM poses. Gyro integration
provides an independent starting orientation for larger turns; final pose comes
from laser points. Multiple starting translations and individual scan pairs check
registration stability. Comparisons must use the lidar offset active during the
test, or explicitly pass `--laser-offset .105 .015` for retrospective correction.

Initial forward tests: wheel odometry 18.0 cm versus laser 7.9 cm, then 13.7 cm
versus 5.7 cm. Initial turning included 35.0° wheel odometry versus 13.8° laser,
and 31.3° wheel odometry versus 6.9° laser during a direction reversal.

After calibration and gyro integration, the first CCW turn was 29.38° odometry
versus 29.34° laser. Subsequent CW turns were within 0.3° of laser heading.
Applying the corrected lidar offset reduced apparent sideways motion during a
held-out CW turn from about 3.5 cm to 1.5 mm.

Forward verification after calibration: 7.49 cm odometry versus 7.61 cm laser
(three initial stationary scans, so treated as preliminary), followed by 7.38 cm
odometry versus 7.98 cm laser (11 before and 12 after scans, 532 matched laser
points, 1.69 mm point-to-line RMS). Individual scan-pair distances were 7.91–8.05 cm.
The remaining distance discrepancy is up to about 8% / 6 mm in these short tests;
this is a useful initial rolling calibration, not a precision mechanical survey.
Longer straight runs and repeated corners remain useful validation of slip and
map stability. Navigation speed settings were not changed in this calibration.

Final live checks passed after restarting SLAM with a fresh in-memory map and
starting navigation: all six navigation lifecycle nodes active, Teensy and
gyro-heading diagnostics OK, one `/odom` publisher at 50 Hz, IMU at 200 Hz,
depth clouds at 15 Hz, lidar at 3.9 Hz, and map updates at 1 Hz. The fresh grid
was 196 × 216 cells at 5 cm resolution. Depth obstacle correspondence was
37/39 cells in the local costmap and 192/235 in the global costmap. Both wheel
velocities and motor powers were zero. Full reports are `final-health.json` and
`final-depth.json` in the TX2 calibration artifact directory. A new navigation
goal around a corner has not been tested since this calibration.

Artifacts on TX2: `/home/operator/calibration-tests/` (raw JSON records, comparisons,
and calibration before/after readback). Local copies: `/tmp/laser-motion-calibration/`.
Damaged map backups: `/home/operator/maps/before-gyro-calibration/map.data` and
`map.posegraph`, plus the earlier `/home/operator/maps/corner-incident/` backup.

## Software checks

Five pure-model tests cover straight/arc integration, optical gyro axis conversion,
bias and wheel-slip handling, stale inputs, and stationary/clock-gap behavior.
An isolated ROS test with `--network none`, domain 88, exercises the actual node,
TF, sensor messages, and output: a 0.4 rad body turn with a falsely high wheel turn
produced 0.4004 rad, with translation and stale-wheel stop also passing.

## Rollback

Stop navigation before changing odometry or geometry. The old compose file is
`/home/operator/calibration-tests/docker-compose-before-gyro.yml`. Remove the
odometry service's added command and bind mounts to use the original image entrypoint.
Restore the first four geometry values from `applied-calibration.json` through
`/base/set_geometry`, then verify `/base/config`. Do not republish the JSON array
directly: that topic takes a Twist, as implemented by the calibration script.

The prior URDF image is `frankjoshua/ros2-urdf:before-gyro-calibration`; the calibrated
image is `frankjoshua/ros2-urdf:calibrated-lidar` (also tagged latest locally).
Restart mapping with a fresh map after changing the odometry origin or lidar TF.
Do not reload the damaged graph as a working map.
