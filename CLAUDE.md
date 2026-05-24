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

## Architecture

### Docker Service Organization
- **docker-compose-ros.yml**: Core ROS 2 software (bridge_suite, slam_toolbox, nav2, diff_drive_controller, urdf, mcp_server)
- **docker-compose-ros-hardware.yml**: Hardware interfaces (micro_ros_agent for Teensy, gps, imu, ydlidar_x4, realsense)
- **docker-compose-mock-hardware.yml**: Mock hardware for testing without a robot — `mock_micro_ros` (echoes `/cmd_vel`→`/vel`) and a world-locked `mock_ydlidar` (box-room `/scan`). See `mock/`.
- **docker-compose-tools.yml**: Development tools (n8n on port 5678, Code-Server on port 8443)

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

All ROS containers use:
- Memory limit: 4GB per container
- Shared memory: 1GB
- Log rotation: 10MB max, 3 files
- Hardware containers use `network_mode: host`, `ipc: host`, `pid: host` for ROS 2 DDS discovery and device access
