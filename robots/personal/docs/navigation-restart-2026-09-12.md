# Navigation restart and traffic handling, September 12, 2026

The owner requested a full restart, then reported a complete recovery spin and
no forward motion despite a displayed path. All original 11 containers were
restarted at about 13:51. The current SLAM graph was saved first to the robot's
calibration-tests/20260912/before-full-stack-restart.{data,posegraph}. SLAM started
a fresh map and odometry origin; wheel calibration and sensor geometry persisted.

Live checks found a distinction the old health report missed: upstream sensor
streams and lifecycle states were healthy, but Nav2's own observation buffers
became many seconds stale. The receive socket reached approximately 16 MiB and
UDP packets were being dropped. Navigation also logged rejected trajectories and
recovery attempts during the owner's goals. The robot was stopped during repair.

Nav2 now runs `ros2-nav2:cyclone-20260912`, built locally from
`navigation/Dockerfile.cyclone`, with `rmw_cyclonedds_cpp` and
`config/tx2-cyclonedds.xml` selecting eth0. The original image is preserved.
A wildcard Fast DDS trial temporarily drained the queue but stale warnings
returned. The underlying Fast DDS fault has not been identified conclusively.
The Cyclone deployment had no stale-observation warnings in the final 20-minute
log window, including the final connected-client checks.

ROS2y required the same middleware for navigation requests. A fresh Fast DDS
client timed out on all six Nav2 lifecycle services, whereas a Cyclone client
received all six active states. The laptop's UFW firewall also blocked direct
robot-LAN DDS packets. The narrowly scoped persistent rule added was:

```
sudo ufw allow in on wlp2s0 from 192.168.8.230 to any port 7400:8000 proto udp comment 'TX2 ROS 2 DDS on robot WiFi'
```

ROS2y's dependency, dev-container settings, `cyclonedds.xml`, and `run_tx2.sh`
were updated in the sibling ros2y repository. Its existing terminal application
was restarted with the new settings; the process environment was verified.
Its read-only self-check receives map, scan, odometry and both footprints; a
separate laptop check received controller state `active` and discovered the
NavigateToPose action server. No driving goal was sent by these checks.

The driver now executes ordinary ROS commands inside a running Nav2 container
so navigation actions match its middleware. Other robot containers still use
Fast DDS and their topic streams interoperate. Native service/action clients
must match the target middleware: the existing Fast DDS rosbridge is not a
verified navigation-action client in this mixed deployment. SLAM serialization
continues to execute inside the SLAM container. A broader middleware migration
has not been performed.

A WLAN INPUT filter preserves separation from the other club robot's domain-0
data and is enabled before Docker on boot. Deployment details are in
[tx2-network-isolation.md](tx2-network-isolation.md).

Two independent load controls were also installed:

- `ros2_depth_nav_relay` forwards the newest complete cloud to
  `/nav/obstacle_points` at up to 5 Hz. This matches the local costmap update rate.
  All eight depth observation sources use this topic. Original depth remains at
  15 Hz. Serialized payloads, camera frame, and source timestamps are preserved;
  no point reduction or obstacle-height change was made. It does not replay old
  frames after a camera outage. It uses one queued input and best-effort QoS.
- The visualization bridge had reached its 3 GiB limit while a client requested
  raw camera views. `bridge_policy/` limits Image/PointCloud2 previews to at most
  2 Hz and one pending sample per subscription. Per-client outgoing websocket
  writes are bounded to 8 MiB; a viewer that cannot keep up is disconnected with
  WebSocket code 1013. Map, TF, IMU and command subscriptions retain their requested
  rates, except point-cloud debug views. These limits apply only to rosbridge;
  native ROS consumers keep their own rates.

The rosbridge adaptation is loaded through PYTHONPATH/sitecustomize only in the
rosbridge_websocket executable. It uses the installed Humble rosbridge class APIs;
run its test when updating that image. The launch log confirms policy loading.
Its isolated test exercises subscription rates, unchanged map/IMU handling, a
blocked writer, the byte limit, overload disconnection, and completed-write
accounting. The isolated depth-relay test checks rate, original bytes/frame/time,
and cessation after input stops. Both passed. Tests publish synthetic data only
in network-none containers with domain 88 where applicable.

No camera geometry, footprint, motor PID, wheel calibration, or collision-check
threshold was relaxed in this repair. New driving goals are needed after the
navigation restarts; a completed physical goal has not yet been verified.

The final `cyclone-final-health.json` check passed: all six lifecycle states
active; odometry 49.6 Hz, lidar 3.94 Hz, wheel feedback 19.35 Hz, IMU 136.5 Hz,
raw depth 15.3 Hz and relayed depth 5.13 Hz. Last received sensor ages were all
under 0.14 s. Teensy/odometry diagnostics were OK and both wheel velocities and
powers were zero. The checker uses serialized cloud subscriptions to avoid
unnecessary Python point-cloud decoding during this timing check. A later
snapshot showed Nav2 134 MiB, bridge 168 MiB, and face HTTP 200.

Evidence is under /home/operator/calibration-tests/20260912/ on the robot.
Use cyclone-final-health.json as the final full health check. Files named
restart-final-health.json and earlier bridge/relay checks were intermediate
experiments and do not prove the Nav2 observation issue was resolved. A full
machine reboot and a completed physical navigation goal remain unverified.
