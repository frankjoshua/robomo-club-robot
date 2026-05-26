# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Robomo.club Robot is a ROS 2 (Humble) mobile robot running on Jetson Nano hardware. The robot uses Docker containers for all ROS services and Ansible for deployment automation.

## Common Commands

### Development Container
```bash
./ros_bash.sh                    # Launch interactive ROS2 Humble container with X11 forwarding
```

### Robot Deployment (via Ansible)
```bash
cd ansible
ansible-playbook -i production ssh.yml -Kk    # First-time SSH setup
ansible-playbook -i production robot.yml      # Deploy/update robot software
ansible-playbook -i production ros.yml        # Deploy ROS software only
ansible-playbook -i production ros_hardware.yml  # Deploy hardware services only
```

### Docker Services
```bash
docker compose -f docker-compose-ros.yml up -d           # Start ROS software services
docker compose -f docker-compose-ros-hardware.yml up -d  # Start hardware interface services
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
- **Physical robot:** target `192.168.33.58:9090` — only after explicitly confirming you want real motion.

The `robomo` robot spec (`utils/robot_specifications/robomo.yaml` in the clone) pre-loads the topic map
(`/cmd_vel`, `/scan`, `/odom`, `/map`, Realsense), Twist control examples, and safety rules.
⚠️ On the real robot, publishing `/cmd_vel` drives the Sabertooth motors — develop against the mock stack
first and always end motion sequences with a zero Twist.

## Architecture

### Docker Service Organization
- **docker-compose-ros.yml**: Core ROS 2 software (bridge_suite, slam_toolbox, nav2, diff_drive_controller, urdf, mcp_server)
- **docker-compose-ros-hardware.yml**: Hardware interfaces (micro_ros_agent for Teensy, gps, imu, ydlidar_x4, realsense)
- **docker-compose-mock-hardware.yml**: Mock hardware for testing without a robot — `mock_micro_ros` (echoes `/cmd_vel`→`/vel`) and a world-locked `mock_ydlidar` (box-room `/scan`). See `mock/`.
- **docker-compose-tools.yml**: Development tools (n8n on port 5678, Code-Server on port 8443)
- **docker-compose-dds-clean.yml**: Shared one-shot `dds_shm_clean` service, pulled into the ROS compose files via `include:`. Before any node starts it purges *orphaned* Fast DDS segments from the host `/dev/shm` (left behind because `ipc: host` containers don't clean up on `down`). Stale segments otherwise OOM-kill a starting node — typically rosbridge, so port 9090 never opens. It deletes only segments no live process maps (checked via `/proc/*/maps`, hence `pid: host`), so it's safe to run while another stack is up (e.g. `ros_hardware` after `ros`).

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

# urdf publishes the static base_link->sensor TF tree
```

### Ansible Structure
- `ansible/production`: Inventory file with robot IP (192.168.33.58)
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
