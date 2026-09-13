# TX2 calibration session, 2026-09-12

Status: refined wheel calibration and lidar alignment applied and saved. A held-out
return test measured 0.13272 m by laser against 0.13148 m odometry (0.94% difference).
It stopped on proximity, with both wheel velocities and motor efforts zero. This
short check supports the correction but does not establish room-scale accuracy.
Chair bases remain close to the route, so no further physical test is scheduled.
Navigation was recreated at 13:40 with the corrected sensor network and a fresh map.

## Current saved calibration

| Setting | Before this session | Applied refinement |
|---|---:|---:|
| Effective counts per revolution | 310000 | 262000 |
| Wheel diameter | 0.1524 m | 0.1524 m |
| Effective turning track | 0.300 m | 0.350 m |
| Maximum RPM setting | 80 | 80 |
| Lidar XYZ | (0.105, 0.015, 1.23) m | (0.106, 0.008, 1.23) m |
| Lidar yaw | 0 | -0.065 rad (-3.72 deg) |

The wheel settings were applied through `driver.sh calibrate-base` and verified
in the Teensy's `/base/config` readback. PID gains and encoder wiring signs were
preserved. Values are saved in EEPROM. The track is an effective rolling value,
not a physical ruler measurement. Lidar height remains inherited/unmeasured.

After the owner cleared the wheel obstruction, two straight closed-loop runs
measured 0.7650 m versus 0.6276 m odometry, and 0.6300 m versus 0.5477 m odometry
(X components before lidar yaw correction). Together with the unobstructed
`forward-highaccuracy` run, the distance-weighted encoder fit gives 262007
counts/rev. The applied rounded value is 262000. These runs imply lidar yaw
corrections from -3.53 to -4.02 degrees; -3.72 degrees was applied. Rotating the
previous motion-derived lidar XY offset into the corrected base axes gives
approximately (0.106, 0.008) m.

The long clear turn measured 2.69024 rad by laser versus 2.69844 rad odometry
(0.47 degree difference), with near-zero center translation. Using the corrected
counts gives a 0.3466 m effective track; 0.350 m was applied. The fit-run distance
residual spread is roughly +/-3%; this is not an independent accuracy guarantee.
The held-out return result below checks the applied settings over a short distance;
a longer unobstructed validation remains useful.

Camera/lidar registration gave inconsistent translation/yaw estimates across
scenes, particularly with people in view. Camera XY/yaw were therefore left
unchanged instead of treating that fit as a reliable mounting measurement.

The old SLAM graph was successfully serialized and copied to
`calibration-tests/20260912/before-refinement.data` and `.posegraph` before the
URDF/SLAM restart. A fresh map prevents mixing the previous lidar orientation
with the corrected one.

## Verified improvements

The D435i was publishing depth but no gyro/accelerometer messages when testing
started. Toggling the IMU streams did not restore samples. A camera hardware reset
restored approximately 200 Hz IMU and 15 Hz depth. `initial_reset: true` is now
saved in `config/realsense-obstacles.yaml`. A second container restart verified
recovery again; allow about 20 seconds for reset and stream startup. Odometry
reports `gyro heading`, with fresh wheel and IMU messages. The Teensy remains
USB-powered only.

Close uncertain depth returns stopped the first short moves. The camera had
visual preset 0 (Custom). Setting `depth_module.visual_preset: 3` (High Accuracy)
allowed longer passes without those stops. This is now persistent and was
checked after restart. It trades fill rate for stricter stereo confidence; it
does not remove the need to check obstacle coverage.

Sources: [RealSense visual presets](https://dev.realsenseai.com/docs/d400-series-visual-presets/),
[depth camera tuning](https://dev.realsenseai.com/docs/tuning-depth-cameras-for-best-performance/),
and [D400 datasheet](https://realsenseai.com/wp-content/uploads/2024/10/Intel-RealSense-D400-Series-Datasheet-October-2024.pdf).
The D435i Min-Z at 640x480 is 175 mm. The calibration guard rejects optical depth
below that range; valid obstacle returns still use the minimum clearance.

## Measurements and exclusion

Raw stationary lidar endpoints were registered independently of SLAM, using
multiple initial translations and individual scan pairs to check consistency.

| Run | Laser translation X | Wheel/gyro odometry X | Laser yaw | Odometry yaw |
|---|---:|---:|---:|---:|
| forward-highaccuracy | 0.5960 m | 0.5132 m | 8.763 deg | 8.582 deg |
| forward-held | 0.7906 m | 0.6964 m | 9.134 deg | 9.445 deg |
| turn-ccw-1 | 0.0204 m | 0.0017 m | 91.51 deg | 91.58 deg |
| turn-ccw-2 | -0.0192 m | -0.0083 m | 69.32 deg | 69.32 deg |
| return-baseline | 0.0335 m | 0.0627 m | -10.94 deg | -10.72 deg |
| return-pass | 0.0292 m | 0.0558 m | -9.78 deg | -9.51 deg |

The outbound runs suggest underestimated rolling distance, but the last portion
of `forward-held` also shows wheel slowing and sudden yaw. **Do not use it or the
obstructed return runs to set calibration.** In the return tests, the right wheel
turned much more slowly and encoders overstated actual motion. The owner then
confirmed the robot was hitting an obstacle at that wheel. This is not evidence
of an encoder or motor defect. These obstructed runs were excluded from the refinement above. Clear outbound
runs supplied the fit. The final held-out return uses fresh endpoints after applying
the calibration and isolating the sensor network.

The guard did not prevent this wheel-level contact. Camera clearance in the
forward field of view and a single lidar plane do not establish clearance of
low objects beside or behind the camera. The observed obstacle coverage needs
further checking; increasing motor power is not a remedy.

## Tooling and next steps

`driver.sh laser-check` now supports bounded longer runs, clockwise/CCW turns,
a named Docker runner, clearance history and stop-point-cloud recording, and
normal closed-loop wheel control with `--closed-loop --speed .08`. It stops on
stale inputs, competing commands, proximity, excess travel/turn/speed/effort.
Straight-run yaw deviation is now capped at 0.08 rad. This diagnostic guard is
not a substitute for complete physical obstacle coverage.

The updated closed-loop runner was exercised in a network-isolated ROS domain with
fake sensors: a one-second ramped command traveled about 0.057 m and stopped; an
obstacle inserted during motion stopped it after about 0.006 m, a remembered low
obstacle stopped it after about 0.116 m, and a duplicate velocity source stopped it
after about 0.057 m. Each case ended with zero speed and effort.
Reproduce with network **none**, ROS_DOMAIN_ID=88 and ROS_LOCALHOST_ONLY=1 using
`diagnostics/test_laser_motion_guard_isolated.py`. Never run that fixture on the
robot's network.

The owner identified office-chair casters as the low obstacles being hit. Both
Nav2 costmaps now have a separate 4 cm vertical voxel layer marking 2.5–60 cm
heights. See [low-obstacles.md](low-obstacles.md) for the isolated regression and
sensing limits. Live depth checks after restart marked all 3 observed local and
all 9 global cells containing points between 2.5 and 5 cm; points between 5 and
12 cm were also marked. These are current depth/costmap correspondences, not a
physical chair-contact avoidance test.

The runner now remembers low points after they leave camera view and uses a
0.15 m/s^2 command ramp. Vectorized obstacle-memory insertion and single-threaded
BLAS prevent the diagnostic calculation starving ROS callbacks. Before that
optimization, two turn attempts stopped on stale data. The successful long turn
had a maximum clearance calculation time of 44 ms. Stale-data protection remains
enabled. The updated isolated runner tests pass normal stopping, immediate
obstacles, remembered low obstacles that disappear from the current cloud, and
duplicate sensor publishers.

## Sensor network correction and held-out check

Another ROS host began publishing `/scan` and `/vel` on the shared club network.
TX2 scans had 1290 ranges, while the additional source had 650. The first refined
return (`return-refined-1`) mixed these streams and is invalid; it was excluded.
The calibration fitting runs used the original single scan layout. See
[tx2-network-isolation.md](tx2-network-isolation.md) for the deployed interface
whitelist and duplicate-source diagnostics. Fresh listeners on both the TX2 and
inside the ROS2y container verified one source for each critical input.

After network isolation, `return-isolated-1` measured:

- Laser translation: X 0.13272 m, Y -0.00132 m; fit RMS 6.0 mm.
- Odometry translation: X 0.13148 m, Y 0.00072 m (0.94% X difference).
- Laser yaw 0.01525 rad versus odometry 0.01140 rad (0.22 degree difference).
- Repeated stationary scan-pair X estimates: 0.13306–0.13450 m.
- Stop reason: obstacle clearance; final wheel velocity and motor power both zero.

The final clearance trigger came from the laser (0.124 m beyond the diagnostic's
padded envelope); remembered low-point clearance was 0.247 m. The scene contains
nearby office-chair bases. This was a guarded calibration stop, not an end-to-end
Nav2 chair-avoidance demonstration. A full-room return and an independent clockwise
turn were not completed. For a future longer check, use fresh stationary endpoints
and a clear route; never reuse endpoints after manually relocating the robot.

## Final running state

The final steady-state health check passed: all six queried Nav2 lifecycle nodes
active, fresh map and map-to-base TF, wheel odometry about 50 Hz, wheel reports
about 20 Hz, IMU about 200 Hz, depth about 15 Hz, laser about 3.9 Hz. Teensy,
encoder-buffer, odometry, ROS-source, and Nav2 diagnostics all report OK. Both
wheel velocities and motor powers were zero. An initial check sampled two nodes
during startup; the subsequent check after activation passed all assertions.

All 11 stack containers run with the selected TX2 DDS profile and automatic
restart policies. The micro-ROS agent is healthy. The face returns HTTP 200 at
`http://tx2.local:8080` from the laptop. A final source audit sees one publisher
for each critical sensor input and only 1290-point scans. ROS2y is visible on the
graph as `rviz_tui`. Container recreation verified process startup with the new
profile; this session did not perform another full machine reboot.

Both live costmaps receive the depth cloud and mark low-height cells. Snapshot
cloud-to-costmap comparisons vary with observation time, cell boundaries, moving
objects, and clearing; some current cloud cells are not lethal. These asynchronous
snapshots do not establish perfect detection coverage. The controlled isolated
regression demonstrates the old/new threshold difference and marking/clearing
behavior. A physical Nav2 test around chair casters remains outstanding.

Raw records and comparisons: local `/tmp/calibration-20260912/`, robot
`/home/operator/calibration-tests/20260912/`.
