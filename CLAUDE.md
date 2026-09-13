# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Robot-specific records are under `robots/club/` and `robots/personal/`; start
with `robots/README.md`. Keep measurements, images and models with their owner.
The root real-hardware Compose configuration currently includes TX2-specific
settings; consult the target robot's config index before deploying.

Personal TX2 power: the user confirms that the Teensy on `tx2.local` is powered
through USB only, with no separate supply (2026-09-12). Unplugging its USB cable
removes its power. Do not apply the older Nano robot's bus-strip/VIN wiring to
the TX2. See AGENTS.md.

Robomo.club Robot is a ROS 2 (Humble) mobile robot running on Jetson Nano hardware (`robmo-club-robot.local` on the LAN — the robot carries its own GL.iNet WiFi router, SSID `ROBOMO-ROBOT-5G`). The robot uses Docker containers for all ROS services and Ansible for deployment automation. (Not to be confused with `tx2.local` — that's Josh's personal TX2 robot, not this one.)

## Common Commands

### Development Container
```bash
./ros_bash.sh                    # Launch interactive ROS2 Humble container with X11 forwarding
# Or open the repo in VS Code → "Dev Containers: Reopen in Container" (.devcontainer/, from docker-ros2-template)
```

### Robot Deployment (via Ansible)
```bash
cd ansible
# These examples select the club; use --limit tx2 for the personal robot.
ansible-playbook -i production ssh.yml --limit robot -Kk  # First-time SSH setup
ansible-playbook -i production robot.yml --limit robot   # Deploy/update software
ansible-playbook -i production ros.yml --limit robot     # ROS software only
ansible-playbook -i production ros_hardware.yml --limit robot  # Hardware services
```

### Docker Services
```bash
docker compose -f docker-compose-ros.yml up -d           # Start ROS software services
docker compose -f docker-compose-ros-hardware.yml up -d  # Start hardware interface services
./start_ros.sh                                           # Run the software stack HERE against the physical robot's hardware (running on robmo-club-robot.local); takes up|down|logs
./start_mock.sh                                          # Run software stack against mock hardware (no robot/Gazebo); takes up|down|logs. See mock/
./start_tools.sh                                         # Start n8n + Code-Server dev tools
```

### Simulation
```bash
cd simulation
./start.sh              # Launch Vagrant VM
./launch_simulation.sh  # Start Gazebo simulator (inside VM)
```

## LLM Access via ros-mcp

Claude Code (and any MCP client) can observe and control the robot in natural language through
[`ros-mcp-server`](https://github.com/robotmcp/ros-mcp-server) — already deployed as the
`ros_mcp_server` container and cloned at `~/development/workspace/ros-mcp-server`. It talks to ROS 2
over the **rosbridge WebSocket (port 9090)** provided by the `ros2_bridge_suite` container — no robot
code changes needed. Tools: list/inspect topics, services & message types, publish/subscribe, call
services, get/set params, and read camera images.

```bash
# One-time: register the MCP server with Claude Code (writes .mcp.json at project scope).
# Runs from the local clone so the robot spec (utils/robot_specifications/robomo.yaml) resolves.
claude mcp add ros-mcp -s project -- uv run --no-sync \
  --directory /home/josh/development/workspace/ros-mcp-server ros-mcp
```

Then bring up a target and connect:
- **Mock / local (safe, no motion):** `./start_mock.sh up`, then ask Claude to *"connect to robomo on 127.0.0.1:9090"*.
- **Physical robot:** target `robmo-club-robot.local:9090` (join the robot's own `ROBOMO-ROBOT-5G` WiFi first; its IP varies by network) — only after explicitly confirming you want real motion.

The `robomo` robot spec (`utils/robot_specifications/robomo.yaml` in the clone) pre-loads the topic map
(`/cmd_vel`, `/scan`, `/odom`, `/map`, Realsense), Twist control examples, and safety rules.
⚠️ On the real robot, publishing `/cmd_vel` drives the Sabertooth motors — develop against the mock stack
first and always end motion sequences with a zero Twist.

## Architecture

### Docker Service Organization
- **docker-compose-ros.yml**: Core ROS 2 software (bridge_suite, face, slam_toolbox, nav2, diff_drive_controller, urdf, mcp_server, diagnostics)
- **ros2_face**: Animated browser face at `http://<host>:8080/` from `frankjoshua/ros2-face`. Subscribes to `/face/expression` (`std_msgs/String`), `/face/gaze` (`geometry_msgs/Point`), and `/face/mouth` (`std_msgs/Float32`). Included in both real and mock software stacks.
- **ros2_diff_drive_controller**: Runs bind-mounted `odometry/wheel_imu_odometry.py`: calibrated `/vel` supplies translation, D435i `/camera/camera/imu` supplies heading. Bias is learned while stationary; stale IMU falls back to wheel heading with a WARN in `/diagnostics`, stale wheels stop integration. Mocks set `use_imu:=false`. Tests: `python3 -m unittest discover -s odometry`; ROS integration test must run with Docker `--network none` and a separate ROS domain. Calibration and rollback: `robots/personal/docs/odometry-calibration.md`.
- **diagnostics/diagnostics_node.py**: Publishes the standard `/diagnostics` (`diagnostic_msgs/DiagnosticArray`, 1 Hz) with one OK/WARN/ERROR status per system plus live readings; logs to `/rosout` only on level changes. First system: `teensy` (from `/vel` + `/joint_states`). Add a system = one check function. Pure decision logic has a self-check: `python3 diagnostics/test_diagnostics.py` inside any Humble env.
- **docker-compose-ros-hardware.yml**: Hardware interfaces (micro_ros_agent for Teensy, gps, imu, ydlidar_x4, realsense)
- **docker-compose-mock-hardware.yml**: Mock hardware for testing without a robot — `mock_micro_ros` (echoes `/cmd_vel`→`/vel`) and a world-locked `mock_ydlidar` (box-room `/scan`). See `mock/`.
- **docker-compose-tools.yml**: Development tools (n8n on port 5678, Code-Server on port 8443)
- **fastdds_udp_only.xml**: Fast DDS profile every ROS container loads via `FASTRTPS_DEFAULT_PROFILES_FILE` (set in each compose file's common anchor). Disables the shared-memory transport — with `ipc: host`, SHM segments in the host `/dev/shm` outlived `down`/`docker restart`/crashes, so there was a cleanup step that `docker restart` bypassed. UDP-only means nothing to clean up. Any ad-hoc `docker run` of a ROS image should mount the file and set the env var too, or it silently falls back to SHM.
- **All images must be the same ROS distro (Humble).** The "OOM on startup / rosbridge never opens 9090 / nav2 stuck Configuring" failures were a mixed stack: stale local Jazzy builds of nav2/slam/urdf/diff-drive next to Humble bridge/lidar/realsense. Jazzy discovery messages make Humble nodes throw `Bad alloc deserializing ParticipantEntitiesInfo` in a loop until they hit the memory cap. If you see that in `docker logs`, check `docker exec <c> ls /opt/ros` across containers and `docker compose pull`. Same applies to any other ROS 2 machine on the robot's LAN with `ROS_DOMAIN_ID=0`.

### Hardware Stack
- **Teensy Microcontroller**: Motor control and encoder feedback via micro-ROS
- **Sabertooth Motor Driver**: Differential drive actuation
- **YDLidar X4**: 360° LIDAR → `/scan` topic
- **Intel Realsense**: RGB-D camera
- **IMU/GPS**: Orientation and location data

### ROS 2 Data Flow
```
# Sensing, mapping, planning
/scan (ydlidar_x4)  -->  slam_toolbox  -->  /map  +  map->odom TF
/map + TF + /scan   -->  nav2          -->  /cmd_vel

# Actuation: the Teensy (via micro_ros_agent) runs the motors
/cmd_vel  -->  micro_ros_agent (Teensy)  -->  Sabertooth motors

# Odometry feedback: the encoders close the loop
Teensy encoders  -->  /vel  -->  diff_drive_controller  -->  /odom  +  odom->base_link TF
#   (/odom and the odom->base_link TF feed back into slam_toolbox and nav2)

# Health: per-wheel telemetry + one status per system
Teensy  -->  /joint_states (wheel angle rad, speed rad/s, drive level -1..1)
/vel + /joint_states  -->  diagnostics  -->  /diagnostics (teensy: OK/WARN/ERROR + readings)

# urdf publishes the static base_link->sensor TF tree
```

### Ansible Structure
- `ansible/production`: Inventory for both robots: `robot` selects the club Nano and `tx2` selects the personal TX2. Use an explicit `--limit`; see each robot's operating notes under `robots/` for its network.
- `ansible/all.yml`: Master playbook (ssh → robot → ros → ros_hardware)
- `ansible/files/udev/`: Hardware device symlink rules (/dev/teensy, /dev/gps, /dev/imu)

## Key Directories

- **apps/**: Standalone ROS 2 Python scripts (robot_info.py, encoder_test.py, square navigation demos)
- **notebooks/**: Jupyter notebooks (diagnostics, PID tuning) and ROS launch/config files
- **simulation/**: Vagrant-based Gazebo simulation environment
- **ansible/**: Infrastructure automation and deployment playbooks
- **sabertooth_settings/**: Motor controller configuration files (.tooth)
- **cad_files/**: 3D printable parts (STL)

## Container Configuration

The `docker-compose-ros.yml` software containers share a common config (`x-common` anchor):
- Memory limit: 3GB per container
- Shared memory (`shm_size`): 3GB
- Log rotation: 10MB max, 3 files
- `network_mode: host`, `ipc: host`, `pid: host` for ROS 2 DDS discovery

Hardware containers (`docker-compose-ros-hardware.yml`) also use host networking/ipc/pid for device access and DDS discovery.

### nav2 runs composed (memory)
The `frankjoshua/ros2-nav2` image launches nav2 as a single composable container by default (its baked-in `nav2_composed.launch.py`; see the docker-ros2-nav2 repo). The stock separate-process bringup makes each of nav2's ~8 nodes its own Fast DDS participant, each independently building discovery state for the whole graph — together they balloon to multiple GB and OOM-kill the container at any limit. Composed, all nodes share one DDS participant: startup stays low (~88 MB), fully activates, and fits the common 3 GB cap with no override.
