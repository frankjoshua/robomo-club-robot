# Robomo.club Robot 2024

Code and documentation for Robomo.club 2019-2024 club robot.

The current robot is living at Arch Reactor in St. Louis, MO (http://archreactor.org).

For more information on our project check out our forum at https://discourse.robomo.club/t/robomo-club-robot-project/82

To see the todo list follow this link. https://github.com/frankjoshua/robomo-club-robot/projects/1

Our website is at http://robomo.club

![Club robot](https://robomo.club/d8938d3ade5b99f15ff5d4e3a885581931a0de5a_1_375x500.jpeg)

# Getting started

These instructions assume you are installing from a linux computer. And that you are on the same network as your robot.

Ansible is used to install and update software on the robot. You must have it installed on your
workstation, and you must complete the [SSH setup](#ssh-setup-assuming-you-are-working-from-a-linux-computer)
below **first**: the inventory refers to the robot only by the ssh alias `robot`, so Ansible can't
reach it until that alias exists in your `~/.ssh/config`.

/ansible/production --> Inventory. Addresses the robot only as the ssh alias "robot" (no IP in this file); also sets local_user "operator". (Its ros_ip/ros_master_uri vars are stale ROS 1 leftovers.)
/ansible/robot.yml --> Playbook for robot software
/ansible/ssh.yml --> Installs ssh keys for user "operator" (the local_user set in /ansible/production)
/ansible/files/ssh_keys --> Public and private keys for user "operator"

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

Then edit the file ~/.ssh/config (create if it doesn't exist) and add the following lines.
`robmo-club-robot.local` is the robot's mDNS name (from its hostname) — unlike a raw IP it
survives DHCP changes and moving between networks, so prefer it. (Substitute a raw IP only if
mDNS is blocked on your network, or use 127.0.0.1 if you are installing on the local system.)

```
Host robot
HostName robmo-club-robot.local
User operator
IdentityFile ~/.ssh/robot_id_rsa
```

**Finding the robot:** the robot carries its own WiFi router (a GL.iNet, SSID `ROBOMO-ROBOT-5G`,
LAN 192.168.8.0/24). Join that WiFi and the Jetson answers at `robmo-club-robot.local`. Verify
with `ping robmo-club-robot.local` — if the name doesn't resolve, the robot is powered off /
still booting, or you're on a different network than the robot. Note that mDNS doesn't cross the
robot router's NAT: sitting on the makerspace LAN won't find a robot that's attached to its own
router (or vice versa).

Then you should be able to ssh into the robot without a password and run sudo commands. If not fix it.

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

On the robot (`robmo-club-robot.local`), bring up **only** the hardware — not its own software
stack, or you'll have two nav2/slam nodes on one DDS domain:

```bash
ssh robot        # the ~/.ssh/config alias from SSH setup above
cd robomo-club-robot && docker compose -f docker-compose-ros-hardware.yml up -d
```

Then here:

```bash
./start_ros.sh          # 'up' (default), 'down', or 'logs'
```

This runs the software stack (`docker-compose-ros.yml`) — slam_toolbox, nav2,
diff_drive_controller, the urdf/TF publisher, rosbridge and the MCP server — against the robot's
sensors and motors, plus the robot-model overlay (`docker-compose-model.yml`) so the robot
renders in Foxglove. As with `start_mock.sh`, `up` aborts if a session of the other mode is still
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
renders in Foxglove Studio. Included by both `start_mock.sh` and `start_ros.sh`.

| Container | What it does |
|-----------|--------------|
| `ros2_urdf` (override) | Swaps the image to plain `ros:humble-ros-base` running `robot_state_publisher` on the bind-mounted `model/robomo.urdf`. |
| `model_meshes` | Serves `model/meshes/` over HTTP on port **8100** — rosbridge can't resolve `package://` mesh URIs, so the URDF references `http://localhost:8100/...` and Foxglove fetches them directly. Also serves the URDF itself at `http://localhost:8100/robomo.urdf`. |

In Foxglove, point the 3D panel's **URDF layer at that URL**, not at the `/robot_description`
topic: the topic is published once (latched) by `robot_state_publisher`, and rosbridge never
replays latched messages to websocket clients that subscribe later — so the topic source only
renders if Foxglove was already connected when `ros2_urdf` started, while the URL always works.
Easiest is to import [`foxglove_layout.json`](foxglove_layout.json) (Foxglove → Layout →
**Import from file**): a preconfigured 3D panel with the URDF layer, `/scan`, `/map`, `/plan`,
and click-to-publish nav2 goals on `/goal_pose`.

### Dev tools — `docker-compose-tools.yml` (`./start_tools.sh`)

| Container | Image | What it does |
|-----------|-------|--------------|
| `n8n` | [n8nio/n8n](https://n8n.io) | Workflow automation UI on port **5678**. |
| `code-server` | [linuxserver/code-server](https://github.com/coder/code-server) | VS Code in the browser on port **8443**. |

To control the running stack (drive, send nav2 goals, echo topics), see the
[`run-robomo-club-robot`](.claude/skills/run-robomo-club-robot/SKILL.md) skill.

# Hardware

A tall differential-drive robot: a **Jetson Nano** running the ROS 2 stack, a
**Teensy 4.0** handling the real-time drivetrain, and a set of USB sensors. A
vertical pole carries the LIDAR (~1.23 m up) and an electronics shelf (~0.6 m).

## System block diagram

```text
  Jetson Nano  "robmo-club-robot"  ·  Ubuntu 18.04 / L4T  ·  Docker  ·  ROS 2 Humble
  (runs the containers listed under "Containers" above)
    │
    └─ USB ─┬─ Teensy 4.0 ........ /dev/teensy   (16c0:0483)   drive motors + wheel encoders
            ├─ YDLidar X4 ........ /dev/ttyUSB0  (CP210x)      360° laser  → /scan
            ├─ Intel RealSense ... (planned)                   RGB-D camera — future addition
            ├─ Pico + IMU ........ /dev/imu      (239a:8120)   WIP — not yet hooked up
            └─ u-blox GPS ........ /dev/gps      (1546:01a7)   u-blox 7 · GNSS fix
```

The USB devices fan out of a **j5create USB 3.0 hub** (clear parts tray on the mid
shelf). For the robot's face there's an **Acer monitor** on the mast (video from the
Jetson) plus a **Logitech K400 Plus** wireless keyboard/touchpad for on-robot debugging
(its USB receiver plugs straight into the Jetson, not the hub).

## Compute

| | |
|---|---|
| Board | NVIDIA Jetson Nano — hostname `robmo-club-robot`, arm64 |
| OS | Ubuntu 18.04 / L4T |
| Runtime | Docker 20.10; the ROS 2 Humble stack runs as the containers in [Containers](#containers) |
| Network | carries its own GL.iNet WiFi router (SSID `ROBOMO-ROBOT-5G`, LAN 192.168.8.0/24) — the Jetson is wired to it over ethernet; join the WiFi and the Nano answers at `robmo-club-robot.local` (mDNS) |

## USB / serial devices

Each device is pinned to a stable `/dev` symlink by the udev rules in
[`ansible/files/udev/`](ansible/files/udev/) (matched on USB vendor/product ID), so
the driver containers always find them regardless of enumeration order:

| Device | USB VID:PID | `/dev` symlink | Driver container | ROS interface |
|--------|-------------|----------------|------------------|---------------|
| Teensy 4.0 (motors + encoders) | `16c0:0483` | `/dev/teensy` | `ros2_micro_ros_agent` | subscribes `/cmd_vel`, publishes `/vel` |
| YDLidar X4 | CP210x | `/dev/ttyUSB0` | `ros2_ydlidar_x4` | `/scan`, `/point_cloud` |
| Intel RealSense _(planned)_ | Intel `8086:…` | (USB) | `ros2_realsense` | RGB-D camera — **future addition**, not yet on the robot |
| IMU on a Pico / RP2040 _(WIP)_ | `239a:8120` | `/dev/imu` | `ros2_imu` | **not yet hooked up** — the Pico emits JSON over serial (work in progress) |
| u-blox GPS (u-blox 7) | `1546:01a7` | `/dev/gps` | `ros2_gps` | GNSS fix |

> The Teensy's bootloader enumerates separately as `16c0:0478` (NXP `1fc9:013x`);
> [`reset_teensy.sh`](reset_teensy.sh) uses that to reset the Teensy with no physical access.

## Drive: motor control & wheel odometry

The drive base is a salvaged **"Little Rascal" power-wheelchair base** — its 24 V
gearmotors (specific model unknown) driven by the Sabertooth.

The Teensy 4.0 runs the closed speed loop. It takes `/cmd_vel`, converts it to
per-wheel targets (differential-drive kinematics), runs a PID against the encoder
feedback, and commands the **Sabertooth 2x32** motor driver over **`Serial2` at 9600 baud
in Sabertooth "Simplified Serial"** — one byte per side (left = Sabertooth M1 = bytes
1–127, right = M2 = bytes 128–255). It reads the wheel encoders through the dual
LS7366R and publishes the measured wheel velocity as `/vel`, which
`diff_drive_controller` integrates into `/odom`.

```text
  /cmd_vel ─► micro_ros_agent ─► Teensy 4.0 ───────────────► Sabertooth ─► L / R motors
   (Twist)      (USB serial)     kinematics + PID             Serial2 9600     │
                                      ▲                                         │ turn
                                      │ measured wheel speed                    ▼
                                 Dual LS7366R ◄── quadrature A/B ◄──── wheel encoders
                                  (SPI counts)
                                      │
   /vel  ◄── Teensy publishes ───────┘
   /odom ◄── diff_drive_controller ◄── /vel
```

Drive geometry (from the firmware [`src/main.cpp`](https://github.com/frankjoshua/micro-ros2-teensy-4-encoders-srf04/blob/master/src/main.cpp), "indoor robot" preset):

| Parameter | Value |
|-----------|-------|
| Drive base | salvaged "Little Rascal" power-wheelchair base (24 V gearmotors) |
| Base type | differential drive |
| Wheel diameter | 0.15 m |
| Wheel track (left ↔ right) | 0.35 m |
| Max motor RPM | 80 |
| Encoder counts / rev (x4) | 130000 |

Sabertooth configuration lives in [`sabertooth_settings/`](sabertooth_settings/)
(Dimension Engineering DEScribe `.tooth` files).

## Wheel encoder wiring (Teensy ↔ dual LS7366R)

The Teensy ([micro-ros2-teensy-4-encoders-srf04](https://github.com/frankjoshua/micro-ros2-teensy-4-encoders-srf04))
reads the wheel encoders through a **dual LS7366R** quadrature counter board: two
LS7366R chips (one per wheel) on a shared SPI bus with separate chip-selects. The
encoders themselves are **HC-020K** slotted optical sensors mounted on the motors
(ahead of the gearbox) — which is why the per-wheel count is so high (130000 in x4).

```text
  TEENSY 4.0                       DUAL LS7366R BOARD                  ENCODERS
  ──────────                       ──────────────────                  ────────

  pin 13  SCK  ─────────────►  SCK  ┐
  pin 11  MOSI ─────────────►  MOSI ├── one SPI bus, shared by both chips
  pin 12  MISO ◄─────────────  MISO ┘
  3V3          ─────────────►  VCC      power both chips at 3.3 V
  GND          ─────────────►  GND

  pin 6   CS   ─────────────►  SS1 ──► LS7366R #1 (LEFT)  ──► A B (I) ──► LEFT  encoder
  pin 5   CS   ─────────────►  SS2 ──► LS7366R #2 (RIGHT) ──► A B (I) ──► RIGHT encoder

  Arrows show signal direction.  A/B = quadrature channels, I = index (optional).
  SCK/MOSI/MISO/VCC/GND are common to both chips; only the CS lines differ.
```

> ⚠️ The Teensy 4.0's pins are **not 5 V tolerant** — run the board logic at 3.3 V
> or level-shift the SPI lines.

Full pin table and firmware details (x4 mode, `TICKS_PER_REVOLUTION`, the
SuperDroid Encoder-Buffer-Library) are in the
[Teensy firmware README](https://github.com/frankjoshua/micro-ros2-teensy-4-encoders-srf04#hardware-dual-ls7366r-quadrature-encoder-buffer).

## Coordinate frames & dimensions

The static sensor transforms come from the URDF
([`model/robomo.urdf`](model/robomo.urdf)); `slam_toolbox` adds `map`→`odom` and
`diff_drive_controller` adds `odom`→`base_link`, so the full chain is
`map → odom → base_link → sensors`.

```text
  map ─► odom ─► base_link ─┬─ base_footprint   ( 0.00,  0.00, 0.00 )  ground projection
   (slam) (diff_drive)      ├─ laser_frame      ( 0.03,  0.00, 1.23 )  YDLidar, top of pole
                            ├─ camera_link      ( 0.31,  0.00, 0.28 )  RealSense, front, fwd
                            │    └─ camera_optical_frame               REP-103 optical frame
                            ├─ imu_link         ( 0.05,  0.08, 0.594)  electronics shelf
                            └─ gps_link         ( 0.07, -0.02, 0.60 )  electronics shelf
```

| Frame | Parent | xyz (m) | Sensor |
|-------|--------|---------|--------|
| `base_footprint` | `base_link` | 0, 0, 0 | ground projection |
| `laser_frame` | `base_link` | 0.03, 0, 1.23 | YDLidar X4 |
| `camera_link` | `base_link` | 0.31, 0, 0.28 | Intel RealSense _(planned)_ |
| `imu_link` | `base_link` | 0.05, 0.08, 0.594 | IMU _(WIP)_ |
| `gps_link` | `base_link` | 0.07, -0.02, 0.60 | GPS |

**Overall size:** ≈ 0.50 m W × 0.91 m L × 1.22 m H (19.5 × 36 × 48 in) — the 1.22 m
height matches the lidar on top of the pole. Drive geometry: 0.15 m wheels on a
0.35 m track (see [Drive](#drive-motor-control--wheel-odometry) above).

## Power

- **Battery:** two 12 V lead-acid batteries in series → a **24 V** pack (the
  wheelchair base's batteries). An onboard **24 V lead-acid charger** rides on the
  lower shelf — its AC cord plugs into the wall and it feeds the pack through an
  XLR charge port.
- **Distribution:** the pack lands on labeled screw-terminal bus strips under the
  top deck — **`24V`** and **`GND`** — with an inline fuse block and a DC wattmeter
  (V / A / W / Wh LCD) on the 24 V side.
- **Motors:** the 24 V bus feeds the **Sabertooth 2x32** (`B+`/`B-`), which drives
  the wheelchair gearmotors. The 24 V motor feed runs through **two E-stops in
  series** — the red twist-release **E-stop mushroom** on the top deck and a
  **car-battery-style remote kill switch** (with keyfobs) — either one cuts motor
  power.
- **5 V rail:** 24 V runs up the mast to the mid-pole power board: a **TOBSUN
  EA50-5V** (24 V → 5 V, 10 A) whose output runs past a 3-digit LED voltmeter,
  then back down to deck bus strips labeled **`5V`** / **`GND`**. (An LC
  noise-filter board used to sit on this rail but has been removed.) That rail
  powers the Jetson Nano and the GL.iNet router; the Teensy and the USB sensors
  draw from the Jetson over USB.
- **Display:** a second DC-DC brick under the top deck (black, "DC Input / DC
  Output" label) powers the Acer monitor.

```text
  wall AC ─► 24 V lead-acid charger ─► XLR charge port ─┐
             (rides on the lower shelf)                 │
                                                        ▼
  2 × 12 V lead-acid, in series (inside the base) ─► 24 V pack
                                                        │
                           [24V] · [GND] bus strips ────┤ ◄── fuse block · DC wattmeter (V·A·W·Wh)
                           (under the top deck)         │
       ┌────────────────────────────┬───────────────────┴───┐
       ▼                            ▼                       ▼
  E-stop mushroom (top deck)  DC-DC brick (? V)       24 V up the mast (mid-pole power board)
       ▼                            │                       │
  remote kill switch (keyfobs)      ▼                       ▼
       ▼                       Acer monitor      TOBSUN EA50-5V (24 V → 5 V, 10 A)
  Sabertooth 2x32                                           │
       ▼                                         "5.15" LED voltmeter
  L / R gearmotors                                          │
                                                [5V] · [GND] deck bus strips
                                                            │
                                       ┌────────────────────┴───┐
                                       ▼                        ▼
                                 Jetson Nano ─ ethernet ─► GL.iNet router
                                       │
                                       └─ USB ─► hub ─► Teensy · YDLidar · GPS  (bus-powered)
```

> ⚠️ Still worth verifying with a meter: the fuse block's rating and exact
> position, and the second DC-DC brick's output voltage. (Confirmed on-site
> 2026-08-08: both E-stops sit in series in the 24 V motor feed and cut power —
> the mushroom and the keyfob kill switch; the router runs from the 5 V rail; the
> LC noise filter has been removed.)

## Bill of materials

As built, July 2026 (photo survey + repo docs). Quantities are per robot; salvage
and shop-stock items have no meaningful part number.

| Subsystem | Part | Qty | Notes |
|-----------|------|-----|-------|
| Drive | Salvaged "Little Rascal" power-wheelchair base — frame, 2 × 24 V gearmotors, drive wheels, casters | 1 | donates the whole drivetrain |
| Drive | 12 V sealed lead-acid battery | 2 | in series → 24 V pack, live inside the base (capacity unrecorded) |
| Drive | Dimension Engineering **Sabertooth 2x32** dual motor driver | 1 | under the top deck; Simplified Serial 9600 baud from the Teensy; config in [`sabertooth_settings/`](sabertooth_settings/) |
| Drive | HC-020K slotted optical encoder | 2 | on the motor shafts, ahead of the gearboxes |
| Control | **Teensy 4.0** on a screw-terminal breakout board | 1 | top deck; micro-ROS node at `/dev/teensy` |
| Control | Dual **LS7366R** quadrature-counter board | 1 | SPI to the Teensy — see [encoder wiring](#wheel-encoder-wiring-teensy--dual-ls7366r) |
| Compute | NVIDIA **Jetson Nano** dev kit | 1 | rear shelf in a laser-cut plywood case; runs the Docker stack |
| Compute | GL.iNet travel router (SSID `ROBOMO-ROBOT-5G`) | 1 | the robot's own WiFi AP |
| Compute | j5create USB 3.0 hub | 1 | clear parts tray, mid shelf — fans out the Jetson's USB |
| Sensors | YDLidar **X4** + its USB adapter board | 1 | top of the mast (`laser_frame`, 1.23 m up) |
| Sensors | u-blox 7 USB GPS | 1 | electronics shelf |
| Sensors | Pico + IMU _(WIP)_ · Intel RealSense _(planned)_ | — | not wired in yet — see [USB / serial devices](#usb--serial-devices) |
| Power | **TOBSUN EA50-5V** DC-DC converter (24 V → 5 V, 10 A) | 1 | mid-pole power board |
| Power | 3-digit LED voltmeter | 1 | mid-pole power board — watches the 5 V rail (~5.15 V) |
| Power | DC multifunction wattmeter (V / A / W / Wh, blue LCD) | 1 | under the top deck, on the 24 V side |
| Power | DC-DC converter brick #2 ("DC Input / DC Output" label) | 1 | under the top deck → Acer monitor (output voltage unrecorded) |
| Power | Inline fuse block (orange) | 1 | 24 V side — rating unrecorded |
| Power | Twist-release E-stop mushroom button | 1 | top deck — in series in the 24 V motor feed |
| Power | Car-battery-style remote kill switch + keyfobs | 1 | in series with the mushroom — either one cuts motor power |
| Power | 24 V lead-acid battery charger + XLR charge port | 1 | onboard, lower shelf — plug the robot into the wall to charge |
| Power | Screw-terminal bus strips (`24V` · `GND` · `5V`) | 4+ | plus ring/fork crimps, wire nuts, split loom |
| HMI | Acer LCD monitor (robot face) | 1 | pole-mounted behind a clear guard; video from the Jetson |
| HMI | Logitech K400 Plus wireless keyboard + touchpad | 1 | USB receiver plugged straight into the Jetson |
| Structure | Plywood decks & mast boards (painted black), steel pipe mast + floor flange, U-bolt cable guide | — | shop-built |
| Structure | Pool-noodle bumpers, zip ties, velcro | — | soft edges for demos |

# Contributors:

Mark Moran<br>
Joshua Frank
