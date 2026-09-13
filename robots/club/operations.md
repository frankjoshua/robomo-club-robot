# Club robot operating notes

Record scope: club Nano robot; compiled from repository documentation on
2026-09-13, without reconnecting to the robot.

Join **ROBOMO-ROBOT-5G** and use `robmo-club-robot.local`. The existing SSH alias
`robot` is intended for this host, and Ansible uses the inventory name `robot`.
Check the alias before deployment; it is workstation configuration, not a robot ID.
Use `--limit robot` with the shared Ansible inventory to avoid selecting the TX2.

The club router and personal router have both used 192.168.8.0/24. Joining
`josh-robot` reaches the personal robot instead. A shared subnet number is not
proof that you are on the correct robot's LAN.

Shared services expose the face on port 8080 and rosbridge on 9090 when running.
The [legacy project guide](../../docs/legacy/project-guide.md) preserves the
original setup and service instructions. Check the [config index](config/README.md)
before using shared deployment files: current real-hardware Compose defaults
include TX2-specific settings. No deployment or running-service changes were made
as part of this repository organization.
