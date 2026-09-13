# RealSense obstacle avoidance — September 11, 2026

The TX2 runs `ros2-realsense:d435i` (SDK 2.56.5 / ROS wrapper 4.56.4) through
`docker-compose-ros-hardware.yml`. The D435i serial is 943222072279, firmware
5.12.1, USB3. Its `/dev/bus/usb` directory is bound into Docker so USB device
numbers can change without leaving a stale device mount. Camera autosuspend is
disabled by the deployed udev rules, including `autosuspend_delay_ms=-1`.

`config/realsense-obstacles.yaml` selects 640×480 at 15 FPS, decimates depth by 4,
and enables untextured point clouds plus color and combined gyro/acceleration.
This ARM SDK exposes `pointcloud__neon_.enable`, not the usual `pointcloud.enable`;
the config supplies both prefixes. Raw depth is 160×120 after decimation.
Large ROS messages use UDP-only Fast DDS with 8 MiB buffers on both participants
and matching host socket limits from `ansible/ros_hardware.yml`.

## Geometry and navigation

The camera uses `camera_name:=camera` so its `camera_link` connects to the existing
URDF tree. A floor-plane fit estimated mounting height 0.420 m, roll 0.0193 rad,
and pitch 0.0208 rad. These replace the old unmeasured 0.28 m/level values. The fit
used 2,303 depth points within 15 mm of the plane; the transformed floor is now
near z=0. Forward offset 0.31 m is retained from the model. These are initial
sensor-based estimates, not a tape-measure mounting survey; recheck if the mount moves.

Both Nav2 costmaps use a separate `depth_layer` voxel grid: 16 cells × 0.125 m,
0–2 m high. Marking uses 0.05–1.95 m obstacle heights and a 2.5 m maximum range.
Clearing includes floor points and raytraces to 3 m. Separate layers keep high
lidar rays from erasing low camera obstacles. Lidar and camera freshness are
required. The depth layer covers the camera's field of view; it cannot see behind
the robot or provide drop-off detection. These are Nav2 costmaps, not additions
to the lidar SLAM map. Direct teleop does not use the Nav2 planner.

## Verified on the robot

After camera and navigation restarts:

- Depth: 300 valid images in 20 seconds, 14.99 Hz, 160×120.
- Color: 300 valid images in 20 seconds, 14.99 Hz, 640×480.
- IMU: 3,989 valid samples, 199.49 Hz, increasing timestamps.
- Point cloud: 15.04 Hz, ~17,500 valid points, ~0.10 s newest-message age.
- Cloud obstacle cells marked lethal: 236/242 inside the local costmap and
  255/288 in the global costmap in the observed scene. Before adding the depth
  layer only 14/234 local candidate cells were lethal.
- Nav2 lifecycle manager reports all managed nodes active. Both costmaps list
  `scan` plus `depth_mark depth_clear`. No stale-camera/TF warnings in the live check.

The IMU reports missing factory calibration and stationary acceleration around
9.23 m/s². It streams but is not fused into odometry. T265 recovery remains separate.
Firmware was not flashed during this deployment.

## Regression checks

In the sibling `docker-ros2-nav2` repository, tests run with `--network none`,
`ROS_DOMAIN_ID=88`, and `ROS_LOCALHOST_ONLY=1`; no test commands reach robot motors.

- `DEPTH_WALL=1 WALL_X=3.0 bash tests/run_wall_integration.sh IMAGE`: virtual
  low barrier invisible to lidar; reached 0.6283 m/s, stopped with 0.0674 m
  footprint clearance, goal aborted and final command zero.
- `integration_depth_clearing.py`: floor produced no lethal cells; low obstacle
  produced five lethal cells; after removal those cells cleared to zero.
- `WALL_X=3.0 bash tests/run_wall_integration.sh IMAGE`: lidar regression with
  fresh empty depth clouds.

These validate software behavior, not physical braking or a real obstacle course.
For a read-only live check, copy `diagnostics/check_depth_obstacles.py` into
`ros2_nav`, then run it after sourcing `/opt/ros/humble/setup.bash` in that container.
It samples point clouds, checks TF, and reports corresponding costmap occupancy.

## Deployed images and rollback

On the TX2, Nav2 `:depth-obstacles` is tagged `:latest`; URDF `:depth-mount` is
also tagged `:latest`. Previous images are retained as `:before-depth` for both.
Build artifacts are under `/home/operator/nav-depth` and `/home/operator/urdf-depth`.
Camera Compose/profile backups are in `/home/operator/realsense-obstacles-backup`.
Restore the previous Nav2 image before disabling the camera: the new costmaps
require its stream. Recreate only the affected services with the existing
`ros_software` / `ros_hardware` Compose project names. The saved SLAM map is unchanged.
