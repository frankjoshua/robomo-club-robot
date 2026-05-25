# Mock hardware

Tiny stand-ins for the robot's hardware so the rest of the ROS 2 stack can be run and
poked at on any machine — **no physical robot and no Gazebo required**. They exist to
verify that the containers start, discover each other over DDS, and exchange the topics
they expect.

Two nodes, each a single Python file run inside a vanilla `ros:humble-ros-base` container
(no image build):

| Mock | Replaces | Subscribes | Publishes |
|------|----------|------------|-----------|
| `mock_micro_ros.py` | `ros2_micro_ros_agent` (Teensy) | `/cmd_vel` (`geometry_msgs/Twist`) | `/vel` (`geometry_msgs/Twist`) |
| `mock_ydlidar.py` | `ros2_ydlidar_x4` | `/odom` (`nav_msgs/Odometry`) | `/scan` (`sensor_msgs/LaserScan`) + `base_link`→`laser_frame` TF |

### How the loop closes

`mock_micro_ros` models a **perfect robot**: it echoes the commanded velocity straight
back as the measured velocity — and, like the firmware's 400 ms watchdog, reports zero
once `/cmd_vel` goes quiet (default 0.4 s) so the robot stops instead of coasting away.
`mock_ydlidar` is **world-locked** — it tracks the robot's
pose from `/odom` and re-projects a room with obstacles (outer walls, boxes, pillars)
each scan, so walls and obstacles sweep past correctly as the robot drives.

```
/cmd_vel ──> mock_micro_ros ──> /vel ──> diff_drive_controller ──> /odom + odom→base_link TF
                                                                      │
                                          mock_ydlidar <─────────────┘  (re-projects room+obstacles)
                                               │
                                               └─> /scan ──> slam_toolbox ──> map ; nav2 ──> /cmd_vel
```

Because odometry is perfect and the scan stays geometrically consistent with it,
slam_toolbox builds a stable map — outer walls plus the box and pillar obstacles — and
nav2 can plan around them. Each beam returns the nearest surface, so obstacles occlude
what's behind them. The scene is fixed in the `odom` frame, centred where the robot
starts (default a 20×16 m room; the robot reveals more of it as it drives, since surfaces
past `RANGE_MAX` read as out-of-range). Still a toy, not a physics sim: 2D, no noise,
static obstacles.

Running the mocks **on their own** (no `diff_drive_controller`, so no `/odom`) leaves the
robot at the origin and the scene is fixed — fine for a quick "do the
containers talk?" check.

## Usage

Run the full software stack against the mocks:

```bash
docker compose -f docker-compose-ros.yml -f docker-compose-mock-hardware.yml up
```

Or just the mocks, to inspect the topics by hand:

```bash
docker compose -f docker-compose-mock-hardware.yml up
# in another shell (e.g. ./ros_bash.sh):
ros2 topic echo /scan --once
# drive: publish continuously (> ~3 Hz). Stop the publisher (Ctrl-C) and the robot
# halts within 0.4 s; a single message just nudges it, like the real base.
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}, angular: {z: 0.1}}'
ros2 topic echo /vel        # mirrors what you publish; returns to zero once you stop
```

> Don't run this at the same time as `docker-compose-ros-hardware.yml` — the mocks and
> the real drivers would publish the same topics.

## Tuning (env vars)

Set these under `environment:` for the relevant service in
`docker-compose-mock-hardware.yml`.

**mock_micro_ros**: `CMD_VEL_TOPIC` (`cmd_vel`), `VEL_TOPIC` (`vel`), `VEL_PUBLISH_HZ` (`50`),
`CMD_VEL_TIMEOUT` (`0.4` — seconds of `/cmd_vel` silence before it reports zero, matching the firmware watchdog).

**mock_ydlidar**: `SCAN_TOPIC` (`scan`), `ODOM_TOPIC` (`odom`), `WORLD_LOCKED` (`true` —
set `false` to keep the scene fixed even when `/odom` is present), `LASER_FRAME`
(`laser_frame`), `BASE_FRAME` (`base_link`), `SCAN_HZ` (`10`), `SCAN_SAMPLES` (`720`),
`RANGE_MIN` (`0.12`), `RANGE_MAX` (`12.0`), `ROOM_WIDTH` (`20.0`), `ROOM_LENGTH` (`16.0`),
`OBSTACLES` (JSON list of `["box", cx, cy, w, h]` / `["circle", cx, cy, r]` in metres;
defaults to a built-in furnished-room layout), `PUBLISH_LASER_TF` (`true` — set `false`
when the `urdf` container already provides the `base_link`→`laser_frame` transform).
