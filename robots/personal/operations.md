# Personal TX2 operating notes

Latest recorded deployment: 2026-09-12. This page is an operating record, not a
claim that the robot is currently online.

## Identity and network

Join **josh-robot** and prefer `tx2.local`. Recorded LAN address: 192.168.8.230;
Tailscale fallback: `tx2.stork-spica.ts.net` / 100.96.218.61. SSH user: `operator`.
The remote checkout is `/home/operator/robomo-club-robot`. Ansible inventory name:
`tx2`; use `--limit tx2` to select only the personal robot.

The club's ROBOMO-ROBOT-5G router also uses 192.168.8.0/24. Selecting that Wi-Fi
previously broke direct TX2 access even though the laptop had a plausible address.

## Runtime and clients

Compose project names are `ros_hardware` and `ros_software`; preserve these names
when managing the existing containers. The [configuration index](config/README.md)
identifies active files and the host-specific `.env` values.

- Face: `http://tx2.local:8080/`; rosbridge: `ws://tx2.local:9090`.
- ROS2y: the sibling ros2y repository's `run_tx2.sh` selects Cyclone DDS on the
  robot LAN. The laptop firewall permits TX2 UDP 7400–8000 on its Wi-Fi interface.
- Nav2 uses Cyclone DDS; its action/service clients must match. The existing
  Fast DDS rosbridge is not a verified cross-middleware navigation-action client.
- The micro-ROS agent uses Fast DDS on loopback and the robot LAN, excluding
  Tailscale. Other Fast DDS services retain the separate TX2 profile.
- The 5 Hz `/nav/obstacle_points` relay is required by the configured costmaps;
  original depth remains available at its camera topic.

Use the shared [driver](../../.claude/skills/run-robomo-club-robot/SKILL.md)
for control. Its ordinary commands execute inside a running Nav2 container to
match that container's middleware. Refer to the
[teleop repair record](docs/teleop-diagnostics-2026-09-12.md) for the actual W/X
command and wheel-response verification.

## USB and recovery

The Teensy has no separate power source. Unplugging its USB cable removes power.
The agent supervisor follows `/dev/teensy` across hotplug and checks fresh wheel
messages; a running container alone is not a health check. Repeated USB
connection failures require checking the physical cable/hub as well as software.
See [agent implementation and USB incident history](../../teensy/README.md),
[network isolation](docs/tx2-network-isolation.md), and
[navigation restart record](docs/navigation-restart-2026-09-12.md).

After restarting navigation, send a new goal. Do not confuse startup completion,
healthy incoming sensors, and verified physical navigation; the reports record
which checks were actually performed.
