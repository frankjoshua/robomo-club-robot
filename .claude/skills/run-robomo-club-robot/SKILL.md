---
name: run-robomo-club-robot
description: Run and control the robomo.club ROS 2 robot. Bring up the Docker stack with no physical robot (mock hardware), then drive it with /cmd_vel, send nav2 navigation goals, and listen to topics (/scan, /odom, /map). Use when asked to run/start/launch the robot or stack, drive/teleop the robot, navigate or send a nav2 goal, echo/inspect/listen to ROS topics, or control robomo.
---

# Run & control: robomo-club-robot

A ROS 2 (Humble) robot that runs entirely in Docker containers (nav2, slam_toolbox,
diff_drive_controller, urdf, rosbridge) and is driven over ROS **topics and actions**.
The whole stack runs on any machine with **no physical robot** via the mock hardware
(`mock/`): a fake Teensy that echoes `/cmd_vel`→`/vel`, and a fake lidar that publishes a
world-locked obstacle room on `/scan`.

**The host has no ROS install** — every `ros2` command runs inside a container joined to
the stack's DDS graph. The driver `.claude/skills/run-robomo-club-robot/driver.sh` wraps
that; use it for all control. Paths below are relative to the repo root.

## Prerequisites
- Docker with `docker compose`. The `frankjoshua/ros2-*` images pull on first `up`.
- Nothing to `apt-get` on the host — it's all containers.

## Launch the stack (mocks — no robot)
```bash
./start_mock.sh up        # software + mock hardware; also: down, logs
```
Give nav2 ~20 s to activate. Do **not** run this alongside
`docker-compose-ros-hardware.yml` (the real drivers publish the same topics).

## Control it — driver.sh (agent path)
Everything goes through the driver (it runs `ros2` in a throwaway container on the
stack's network). Run from the repo root:

```bash
D=.claude/skills/run-robomo-club-robot/driver.sh

# listen
$D topics                 # list topics: /scan /odom /map /cmd_vel /goal_pose /tf ...
$D pose                   # robot position from /odom
$D scan                   # one /scan (obstacle-room ranges)
$D echo /odom --once      # any topic, plain `ros2 topic echo` style

# autonomous navigation (nav2)
$D goto 0 0               # publish a goal to /goal_pose (map frame); returns immediately
$D nav 0 0                # via the navigate_to_pose action; waits for SUCCEEDED/ABORTED

# manual teleop  (args: linear angular seconds)
$D drive 0.5 0.0 2        # /cmd_vel linear=0.5 m/s for 2 s, then auto-stop
$D stop                   # zero /cmd_vel
```

Verified outputs (this session, this container):
- `goto 0 0` → `publishing #1: geometry_msgs.msg.PoseStamped(... position=Point(x=0.0, y=0.0...))`
- `nav 0 0`  → `Goal accepted ...` → `Goal finished with status: SUCCEEDED` (robot drove to the origin)
- `drive 0.5 0.0 2` → `drove 2s at lin=0.5 ang=0.0, then stopped`
- `pose` → `x: -2.02  y: 3.85  z: 0.0`
- `scan` → `array('f', [2.547, 2.553, ... 8.444, ...])`  (near surface then a far wall)

## Visualize (GUI, optional)
- **Foxglove Studio** (verified): the stack already runs rosbridge — add a *Rosbridge*
  connection to `ws://localhost:9090`. A 3D panel shows `/map` `/scan` `/tf` and the robot;
  publish a `geometry_msgs/msg/PoseStamped` to `/goal_pose` (Publish panel) to navigate, or
  use a Teleop panel → `/cmd_vel`. (Foxglove has no RViz-style click-on-map goal tool.)
- **RViz** (not verified headless — needs a display): `./ros_bash.sh` opens an X11 ROS
  container; `rviz2 -d rviz.rviz` there gives the "Nav2 Goal" click-to-navigate tool.

## Gotchas
- **Only one thing should drive `/cmd_vel` at a time.** nav2's velocity_smoother, a
  Foxglove Teleop panel, and `driver.sh drive` all publish `/cmd_vel` and fight each other.
  For autonomous nav use `goto`/`nav` (let nav2 own `/cmd_vel`); for manual `drive`, make
  sure nothing else is commanding. A connected Foxglove teleop panel is the usual reason
  the robot appears to "wander" or `drive` seems ignored.
- **The mock has a 0.4 s command watchdog** (mirrors the Teensy firmware): `/cmd_vel` must
  arrive continuously (>~3 Hz) or the robot stops. That's why `drive` publishes at 10 Hz; a
  single `/cmd_vel` message just nudges it.
- **nav2 goals are in the `map` frame** (≈ the odom origin / robot start, via slam).
  `goto` is fire-and-forget; `nav` blocks until the action result.
- **It's mocks, not a simulator**: perfect odometry, a static obstacle room on `/scan`.
  Good for exercising nav2/slam plumbing and paths around obstacles; not for physics.

## Troubleshooting
- **`nav`/`goto` does nothing; `send_goal` hangs on "waiting for action server"** → nav2
  (`ros2_nav`) isn't up/active. `docker ps | grep ros2_nav`; if it exited, `docker start
  ros2_nav` (or `./start_mock.sh up`) and wait ~20 s.
- **nav2 servers OOM-die seconds after start** → you're not on the composed image. The
  `frankjoshua/ros2-nav2` image runs nav2 as a single process on purpose; `./start_mock.sh
  down && up`. (Eight separate nav2 processes blow the 3 GB container cap.)
- **`drive` doesn't move the robot** → another `/cmd_vel` publisher is winning. Stop it
  (close the Foxglove teleop panel, or `docker stop ros2_nav` for pure manual control).
- **No `/odom` or `/map`** → stack not fully up. `./start_mock.sh up`, wait ~20 s, retry.
