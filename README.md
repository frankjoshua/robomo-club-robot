# Robomo.club Robot 2024

Code and documentation for Robomo.club 2019-2024 club robot.

The current robot is living at Arch Reactor in St. Louis, MO (http://archreactor.org).

For more information on our project check out our forum at https://discourse.robomo.club/t/robomo-club-robot-project/82

To see the todo list follow this link. https://github.com/frankjoshua/robomo-club-robot/projects/1

Our website is at http://robomo.club

![Club robot](https://robomo.club/d8938d3ade5b99f15ff5d4e3a885581931a0de5a_1_375x500.jpeg)

# Getting started

These instructions assume you are installing from a linux computer. And that you are on the same network as your robot.

Ansible is used to install and update software on the robot. You must have it installed on your workstation and be able to ssh into the robot from your workstation before continuing.
/ansible/production --> Has hostname and ip address of the robot
/ansible/robot.yml --> Playbook for robot software
/ansible/ssh.yml --> Installs ssh keys for user "robomo"
/ansible/files/ssh_keys --> Public and private keys for user "robomo"

Run this command to install or update the robot
```
cd ansible
ansible-playbook -i production ssh.yml -Kk
ansible-playbook -i production robot.yml
```

# SSH setup (Assuming you are working from a Linux computer)

**\*Do not follow these instructions if your robot is in production or is accessible from the internet. This is for convenience in a shared project.**

First copy the ssh key and fix the file permissions.

```
cp ./ansible/files/ssh_keys/robot_id_rsa ~/.ssh/
chmod 400 ~/.ssh/robot_id_rsa
```

Then edit the file ~/.ssh/config (create if it doesn't exist).
Add the following lines to the file replacing <IP_OF_JETSON_NANO> with the address of the Jetson nano or whatever computer you use. Or use 127.0.0.1 if you are installing on the local system.

```
Host robot
HostName <IP_OF_JETSON_NANO>
User robot
IdentityFile ~/.ssh/robot_id_rsa
```

Then you should be able to ssh into the nano with out a password and run sudo commands. If not fix it.

```
ssh robot
```

# Simulating the robot

Run the full ROS 2 software stack against lightweight mock hardware — a fake Teensy that echoes `/cmd_vel` back as `/vel`, and a world-locked fake YDLidar that publishes a box-shaped room on `/scan`. No physical robot and no Gazebo required: slam_toolbox maps the room and nav2 can navigate it. See [`mock/`](mock/) for details and tunables. The Blender-built robot model ([`model/`](model/)) is layered in as well, so the robot renders in Foxglove Studio (Rosbridge connection, `ws://localhost:9090`).

```bash
./start_mock.sh          # 'up' (default), 'down', or 'logs'
```

The mock and real-robot modes refuse to mix: `up` aborts if a `start_ros.sh` session (or the
hardware drivers) is still up — both modes fight over the same `/vel` and `/scan` topics — and
tells you which `down` to run. This also catches sessions a reboot auto-restarted.

Or bring up individual software containers by hand:

```bash
docker run -it \
    --network="host" \
    --pid="host" \
    --ipc="host" \
    frankjoshua/ros2-bridge-suite
```

```bash
docker run -it \
    --network="host" \
    --pid="host" \
    --ipc="host" \
    frankjoshua/ros2-diff-drive-controller
```

```bash
docker run -it \
    --network="host" \
    --pid="host" \
    --ipc="host" \
    frankjoshua/ros2-urdf
```

# Running the software here against the physical robot

To develop the ROS 2 brains on this laptop while the **real** robot provides the sensors and
motors, run the hardware drivers on the robot and the software stack here. The two machines
discover each other over DDS, so they must be on the same LAN and `ROS_DOMAIN_ID` (default 0).

On the robot (`tx2.local`), bring up **only** the hardware — not its own software stack, or
you'll have two nav2/slam nodes on one DDS domain:

```bash
ssh tx2.local
cd robomo-club-robot && docker compose -f docker-compose-ros-hardware.yml up -d
```

Then here:

```bash
./start_ros.sh          # 'up' (default), 'down', or 'logs'
```

This runs the software stack (`docker-compose-ros.yml`) — slam_toolbox, nav2,
diff_drive_controller, the urdf/TF publisher, rosbridge and the MCP server — against the robot's
sensors and motors. As with `start_mock.sh`, `up` aborts if a session of the other mode is still
up (even one auto-restarted by a reboot) so fake and real sensor topics never mix.

> ⚠️ This drives the **real** motors — publishing `/cmd_vel` turns the wheels. Develop against
> `./start_mock.sh` first and always end a motion sequence with a zero Twist.

# Containers

The robot is a set of single-purpose Docker containers, split across compose files by
concern. Images are published under [`frankjoshua/`](https://hub.docker.com/u/frankjoshua)
on Docker Hub and built from the linked source repos. All use host networking/IPC/PID for
ROS 2 DDS discovery; see [CLAUDE.md](CLAUDE.md) for resource limits.

Every ROS compose file also `include:`s the one-shot `dds_shm_clean` service
(`docker-compose-dds-clean.yml`), which purges orphaned Fast DDS shared-memory segments from
`/dev/shm` before any node starts — leftover segments from a previous run otherwise OOM-kill
nodes (typically rosbridge) on startup. It only runs on `docker compose up`, so prefer a full
`down`/`up` over restarting containers in place.

### Core ROS 2 software — `docker-compose-ros.yml`

| Container | Source | What it does |
|-----------|--------|--------------|
| `ros2_bridge_suite` | [docker-ros2-bridge-suite](https://github.com/frankjoshua/docker-ros2-bridge-suite) | rosbridge WebSocket server (port **9090**) — exposes ROS 2 topics/services/actions to web clients like Foxglove Studio and the MCP server. |
| `ros2_slam_toolbox` | [docker-ros2-slamtoolbox](https://github.com/frankjoshua/docker-ros2-slamtoolbox) | SLAM — builds the map from `/scan` + odometry and publishes the `map`→`odom` transform. |
| `ros2_nav` | [docker-ros2-nav2](https://github.com/frankjoshua/docker-ros2-nav2) | Nav2 autonomous navigation (planning + control). Runs **composed** (all nodes in one process). Consumes `/map`, `/scan`, TF → publishes `/cmd_vel`. |
| `ros2_diff_drive_controller` | [docker-ros2-diff-drive-controller](https://github.com/frankjoshua/docker-ros2-diff-drive-controller) | Integrates wheel velocity (`/vel`) into `/odom` and the `odom`→`base_link` transform. |
| `ros2_urdf` | [docker-ros2-urdf](https://github.com/frankjoshua/docker-ros2-urdf) | `robot_state_publisher` — the robot model (URDF) and the static `base_link`→sensor TF tree. |
| `ros2_mcp_server` | [docker-ros2-mcp-server](https://github.com/frankjoshua/docker-ros2-mcp-server) ([upstream](https://github.com/robotmcp/ros-mcp-server)) | MCP server bridging LLMs to ROS 2 over rosbridge — inspect topics, publish/subscribe, call services, read camera images. |

### Hardware interfaces — `docker-compose-ros-hardware.yml`

One container per device; each maps a `/dev/*` symlink from the udev rules in `ansible/files/udev/`.

| Container | Source | What it does |
|-----------|--------|--------------|
| `ros2_micro_ros_agent` | [docker-ros2-micro-ros-agent](https://github.com/frankjoshua/docker-ros2-micro-ros-agent) | micro-ROS agent for the Teensy (motor control + wheel encoders) over serial (`/dev/teensy`). Subscribes `/cmd_vel`, publishes `/vel`. |
| `ros2_ydlidar_x4` | [docker-ros2-ydlidar-x4](https://github.com/frankjoshua/docker-ros2-ydlidar-x4) | YDLidar X4 360° LIDAR driver → `/scan` (`/dev/ttyUSB0`). |
| `ros2_realsense` | [docker-ros2-realsense](https://github.com/frankjoshua/docker-ros2-realsense) | Intel RealSense RGB-D camera driver. |
| `ros2_imu` | [docker-ros2-imu](https://github.com/frankjoshua/docker-ros2-imu) | IMU driver — orientation (`/dev/imu`). |
| `ros2_gps` | [docker-ros2-gps](https://github.com/frankjoshua/docker-ros2-gps) | GPS receiver driver (`/dev/gps`). |

### Mock hardware — `docker-compose-mock-hardware.yml`

Stand-ins so the full software stack runs with **no physical robot** — plain `ros:humble-ros-base` running the scripts in [`mock/`](mock/). Brought up via [`start_mock.sh`](start_mock.sh).

| Container | What it does |
|-----------|--------------|
| `mock_micro_ros_agent` | Fake Teensy — echoes `/cmd_vel`→`/vel` (perfect velocity tracking + a 0.4 s command watchdog). |
| `mock_ydlidar_x4` | Fake lidar — a world-locked 20×16 m room with obstacles, published on `/scan`. |

### Robot model overlay — `docker-compose-model.yml`

Layers the Blender-built robot model (see [`model/`](model/)) onto the stack so the robot
renders in Foxglove Studio. Included by `start_mock.sh`.

| Container | What it does |
|-----------|--------------|
| `ros2_urdf` (override) | Swaps the image to plain `ros:humble-ros-base` running `robot_state_publisher` on the bind-mounted `model/robomo.urdf`. |
| `model_meshes` | Serves `model/meshes/` over HTTP on port **8100** — rosbridge can't resolve `package://` mesh URIs, so the URDF references `http://localhost:8100/...` and Foxglove fetches them directly. |

### Dev tools — `docker-compose-tools.yml` (`./start_tools.sh`)

| Container | Image | What it does |
|-----------|-------|--------------|
| `n8n` | [n8nio/n8n](https://n8n.io) | Workflow automation UI on port **5678**. |
| `code-server` | [linuxserver/code-server](https://github.com/coder/code-server) | VS Code in the browser on port **8443**. |

To control the running stack (drive, send nav2 goals, echo topics), see the
[`run-robomo-club-robot`](.claude/skills/run-robomo-club-robot/SKILL.md) skill.

# Links

[https://www.dimensionengineering.com/datasheets/KangarooManual.pdf](https://www.dimensionengineering.com/datasheets/KangarooManual.pdf)

# Contributors:

Mark Moran<br>
Joshua Frank
