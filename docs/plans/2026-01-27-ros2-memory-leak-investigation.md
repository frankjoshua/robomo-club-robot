# ROS2 Docker Container Memory Leak Investigation

**Date:** 2026-01-27
**Status:** Investigation in progress
**Priority:** High - blocks all ROS2 development/testing

## Problem Statement

ROS2 Docker containers experience catastrophic memory growth when running together, exhausting 128GB of system memory in approximately 1 minute.

### Conditions to Reproduce
- All ROS2 containers must be running simultaneously
- Memory explosion begins around the time nav2 starts (before receiving navigation goals)
- Individual containers in isolation show no memory issues
- Inter-container message passing appears to be the trigger

### Current Mitigation
4GB memory limit per container (`deploy.resources.limits.memory: 4g` in docker-compose-ros.yml) causes random containers to be OOM-killed, preventing full system crash but not solving the root cause.

### Observed Behavior
- No single container is consistently killed - suggests distributed memory growth across all containers
- Both robot (TX2) and workstation (128GB) experience memory growth simultaneously
- QoS mismatch errors have been observed in logs (specific errors not captured)

## System Architecture

### Distributed Deployment

| Location | Compose File | Containers | Network Mode | Memory Limit |
|----------|--------------|------------|--------------|--------------|
| **Workstation** (128GB) | docker-compose-ros.yml | bridge_suite, mcp_server, slam_toolbox, nav2, diff_drive_controller, urdf | Docker bridge (host commented out) | 4GB |
| **Robot** (TX2, 7.7GB) | docker-compose-ros-hardware.yml | micro_ros_agent, gps, imu, ydlidar_x4, realsense | Host network | None |

### Network Configuration Issue
- **Software containers** (ros.yml): `network_mode: host` is **commented out**
- **Hardware containers** (ros-hardware.yml): `network_mode: host` is **enabled**

This mixed configuration may cause DDS discovery issues between containers.

### DDS Configuration
- ROS2 Humble with default **Fast DDS** middleware
- No explicit DDS tuning or QoS configuration
- Cross-machine DDS discovery over physical network
- Software containers behind Docker bridge NAT

### Data Flow
```
Robot (192.168.33.58)              Workstation
─────────────────────              ───────────────────
ydlidar_x4 ──/scan──────────────► slam_toolbox ──/map──► nav2
                                        │                  │
micro_ros_agent ──/odom─────────► ◄────/tf────────────────│
                                                          ▼
                                                     /cmd_vel
                                                          │
                                       diff_drive_controller
```

## Root Cause Hypotheses

Ranked by likelihood based on evidence:

### Hypothesis 1: QoS Mismatch Causing Unbounded Buffering (HIGH)
**Evidence:** User has observed QoS mismatch errors in logs.

- Publishers and subscribers may have mismatched Quality of Service settings
- If publisher is "reliable" but subscriber can't keep up, messages queue indefinitely
- Network latency between robot and workstation exacerbates this
- Both sides buffer: publisher holds unacknowledged messages, subscriber holds incoming queue

### Hypothesis 2: DDS Discovery Storm (HIGH)
- Fast DDS performs continuous discovery over the network
- Docker bridge NAT may interfere with multicast discovery
- DDS could be repeatedly "finding" and "losing" nodes, accumulating discovery state
- Both sides would see memory growth as discovery metadata accumulates

### Hypothesis 3: TF Buffer Explosion (MEDIUM)
- ROS2 tf2 maintains a time-based buffer of all transforms
- Multiple sources publishing transforms at high rates fills this buffer
- Cross-network latency could cause tf2 to retain more history

### Hypothesis 4: Message Feedback Loop (MEDIUM)
- Some circular dependency causes messages to echo/amplify
- Would cause exponential growth matching the ~1 minute timeline

### Hypothesis 5: Fast DDS Transport Fallback Bug (LOWER)
- Fast DDS prefers shared memory transport when available
- When unavailable (cross-network), fallback to UDP may have buffer leaks

## Research Findings

### Known ROS2/Nav2 Memory Issues

| Source | Issue | Status |
|--------|-------|--------|
| [Nav2 #1889](https://github.com/ros-navigation/navigation2/issues/1889) | Controller/Planner/AMCL leak ~50MB/hour even when idle | Unresolved - blamed on upstream rclcpp/FastRTPS |
| [CycloneDDS #452](https://github.com/ros2/rmw_cyclonedds/issues/452) | Memory grows with multiple nodes, never recovers after CPU load | Partially addressed in Humble |
| [rclpy #643](https://github.com/ros2/rclpy/issues/643) | Python subscriber memory leak | Known issue |
| [CycloneDDS #388](https://github.com/ros2/rmw_cyclonedds/issues/388) | Actions cause leaks (specific to CycloneDDS) | Open |

**Note:** The documented leaks are ~50MB/hour. Our issue is ~2GB/second - orders of magnitude worse, suggesting a different root cause.

### Docker Images
- Base: `ros:humble-ros-base`
- Default DDS: Fast DDS (eProsima)
- No explicit DDS configuration in Dockerfiles

## Debugging Plan

### Phase 1: Baseline Memory Monitoring Setup
1. Create a script to log memory usage per container every second
2. Run on both robot and workstation simultaneously
3. Capture which container grows first and fastest

### Phase 2: Incremental Container Startup
Start containers one at a time with 30-second gaps, monitoring memory:
1. URDF only → stable?
2. Add micro_ros_agent → stable?
3. Add ydlidar → stable?
4. Add slam_toolbox → stable?
5. Add diff_drive_controller → stable?
6. Add nav2 → OBSERVE

### Phase 3: QoS Investigation
1. Run `ros2 topic info <topic> --verbose` to capture QoS settings
2. Compare QoS between publishers and subscribers
3. Identify mismatches and document them

### Phase 4: Network Configuration Fix
1. Enable `network_mode: host` for all software containers
2. Test if this resolves DDS discovery issues
3. Document any changes in behavior

### Phase 5: DDS Configuration Testing
1. Try CycloneDDS instead of Fast DDS
2. Add explicit QoS profiles to force compatible settings
3. Configure DDS buffer limits

## Potential Solutions

### Quick Fixes to Try
1. **Enable host networking** for all containers (uncomment in docker-compose-ros.yml)
2. **Set explicit QoS profiles** with bounded queue depths
3. **Add memory limits** to hardware containers as well

### Longer-term Solutions
1. **Switch to CycloneDDS** - different behavior, may not have same issues
2. **Configure DDS XML profiles** - explicit buffer limits and QoS
3. **Use ROS2 domain bridge** instead of direct DDS discovery across networks

## Files to Modify

- `docker-compose-ros.yml` - network mode, memory limits
- `docker-compose-ros-hardware.yml` - memory limits
- New: DDS configuration XML files
- New: QoS profile YAML files

## Blockers

- **YDLidar hardware issue** - lidar initializes but times out after ~30 seconds. Needs physical attention before testing can proceed.

## Next Steps

1. Resolve YDLidar hardware issue
2. Execute Phase 1 (memory monitoring)
3. Execute Phase 2 (incremental startup)
4. Capture and analyze QoS mismatches
