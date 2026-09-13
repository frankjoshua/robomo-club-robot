# Robot directory

| Detail | [Club](club/README.md) | [Personal](personal/README.md) |
| --- | --- | --- |
| Owner | Robomo club | Josh |
| Computer | Jetson Nano | Jetson TX2 |
| Host | `robmo-club-robot.local` | `tx2.local` |
| Robot Wi-Fi | `ROBOMO-ROBOT-5G` | `josh-robot` |
| Base | Little Rascal wheelchair base | Zagros MAX-14 circular base |
| Physical envelope | Approximate historical dimensions; see specs | Owner-confirmed 0.3556 m diameter |
| Photos | [8 club images](club/images/README.md) | [4 personal images](personal/images/README.md) |
| Models | [Blender, GLB and previews](club/models/README.md) | [Model status](personal/models/README.md) |
| Specs | [Club specs](club/specs.md) | [Personal specs](personal/specs.md) |
| Configuration | [Club config index](club/config/README.md) | [Personal config index](personal/config/README.md) |
| Operating notes | [Club](club/operations.md) | [Personal](personal/operations.md) |

Both Wi-Fi routers have used 192.168.8.0/24. An address in that subnet alone does
not identify the robot. The existing Ansible inventory names are `robot` (club)
and `tx2` (personal).

## Where new material belongs

Use the same structure for each robot: `specs.md` for its current documented
specifications, `operations.md` for access and operating notes, `images/` for
original photos, `models/` for Blender/CAD source and exports, `docs/` for dated
measurements and repair reports, and `config/` for its runtime-file index.
New robot-specific configuration should live in that robot's config directory;
existing deployed root config paths stay authoritative until a deliberate
configuration migration updates their consumers.

Each specification should state its units and evidence: owner-confirmed,
measured, configured, documented historically, photo estimate, or unknown.
A configured value is not automatically a measurement. Keep superseded values
in dated reports, and link the current spec to its source. Treat model dimensions
as visual estimates unless they have independent measurements.

Shared software stays at the repository root. Shared component designs belong in
[docs/shared/](../docs/shared/README.md), with installation status stated explicitly.
Do not copy wheel calibration, sensor transforms, power wiring, or model geometry
between the robots merely because they use similar electronics.
