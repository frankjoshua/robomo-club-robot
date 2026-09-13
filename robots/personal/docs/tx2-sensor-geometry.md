# TX2 geometry audit — 2026-09-12

Later measured driving refined the lidar to XYZ (0.106, 0.008, 1.23) m and yaw
-0.065 rad. See [the calibration report](calibration-2026-09-12.md). The sections
below record the earlier footprint/floor audit; camera geometry remains unchanged.

The face was upgraded from `6cf7c97` to `ed0ef4c`, built from the published
`face-diagnostics` branch. All 27 server tests and eight browser tests passed;
HTTP content and the deployed image revision were checked, and the kiosk was
refreshed. Rollback image: `ros2-face:before-update-20260912` on the TX2.

## Camera floor measurement

Six D435i depth point clouds were transformed into `camera_link`, independent
of the configured camera-to-base height. Each floor fit had 2,839–2,854 inliers,
about 3 mm RMS plane residual, and spanned over 2 m in both horizontal axes.
Estimated heights ranged from 0.3927 to 0.4004 m; median 0.3979 m. This spread
and depth calibration limit accuracy; 3 mm residual is not absolute accuracy.

`config/tx2.urdf` now uses camera height **0.398 m**, roll **0.0123 rad**, and
pitch **0.0125 rad**, replacing 0.420 m / 0.0193 rad / 0.0208 rad. Camera X/Y are now estimated as 0.105/0.015 m, aligned beneath the
front laser based on the owner's description. The owner confirmed all parts
fit inside the 14-inch base, ruling out the inherited X=0.31 m value. A floor
plane does not measure horizontal mount position; this alignment is an estimate. The runtime URDF is bind-mounted through `docker-compose-ros.yml`.

The measurement report is saved on the TX2 at
`~/calibration-tests/geometry-20260912.json`.

## Conflicting laser transforms corrected

The vendor `ydlidar_launch.py` started `static_tf_pub_laser`, publishing
`base_link -> laser_frame` at (0, 0, 0.02) m. This conflicted with the robot
description at (0.105, 0.015, 1.23) m. A fresh TF listener actually received
the centered 2 cm transform, so this was an active conflict, not only stale
documentation.

Hardware Compose now runs the lidar driver directly with its existing parameter
file. Only robot_state_publisher supplies the laser mounting transform. The
front offset (0.105, 0.015) m comes from the earlier motion calibration. The
1.23 m height is an inherited value and still needs a physical measurement for
this TX2. The user says the laser is at the front, above the RealSense; obtain
the vertical separation and any horizontal difference before changing those
coordinates. Do not infer laser height from the camera's floor plane.

After deployment, a fresh ten-second listener received 39 laser scans and
142 depth clouds, with newest cloud age 0.083 s. It saw only the model's laser
transform and the updated camera height. `/tf_static` publishers were
`robot_state_publisher` and `camera`; the conflicting laser publisher was gone.

## Doorway footprint correction

At the start of the audit, both live Nav2 costmaps used a 0.32 m radius (64 cm diameter), 0.01 m footprint
padding, a 0.55 m inflation radius, and cost scaling 3.0. The owner-provided
[Zagros MAX 14 base](https://www.zagrosrobotics.com/shop/item.aspx?itemid=688)
has a 14-inch deck (35.56 cm), confirmed by its
[dimensioned drawing](https://www.zagrosrobotics.com/drawings/REX-14D-RND-B.PDF).
The product page's parenthetical 30.5 cm conflicts with its inch dimension;
the drawing explicitly says 14 inches.

The owner subsequently confirmed that **everything fits inside the round base**.
`config/tx2-nav2.yaml` now uses radius **0.1778 m** and padding **0.02 m** on both
costmaps (35.56 cm physical diameter, approximately 39.56 cm with padding).
Inflation stays at 0.55 m / scaling 3.0; the corrected body size is the first fix.
The parameter file is bind-mounted into the Nav2 container, surviving reboot.
The circular footprint retains DWB's appropriate `BaseObstacle` critic.

Inflation is a graded obstacle cost, not an additional 55 cm hard body margin.
There are no reported protrusions requiring a polygon footprint.

### Verification after footprint correction

`diagnostics/check_doorway_isolated.py` runs Nav2 with synthetic lidar, depth,
odometry, and a map in Docker `--network none`, `ROS_DOMAIN_ID=88`, and
`ROS_LOCALHOST_ONLY=1`. It cannot reach the robot's ROS graph.

| Configuration | Door width | Result |
|---|---:|---|
| Previous 0.32 m radius | 0.60 m | Planner aborted; no movement |
| Corrected 0.1778 m radius + 0.02 m padding | 0.60 m | Planned and navigated through; minimum simulated physical clearance 0.100 m |
| Corrected footprint | 0.30 m | Planner aborted; no movement |

After recreating Nav2 and restarting robot_state_publisher, live parameter
queries confirmed the new radius/padding on both costmaps. All six navigation
lifecycle nodes were active. A fresh TF listener confirmed camera XYZ
(0.105, 0.015, 0.398) m and laser XYZ (0.105, 0.015, 1.23) m. The camera's XY
alignment and retained laser height are estimates, not new physical measurements.

No physical navigation test was performed. The Teensy USB device was absent
during this audit; it is USB-powered, with no separate supply.
