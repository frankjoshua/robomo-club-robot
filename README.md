# Robomo robots

This repository contains shared ROS 2 software and separate records for the
**Robomo club robot** and **Josh's personal robot**.

| Robot | Identity | Records |
| --- | --- | --- |
| Club | Jetson Nano, Little Rascal wheelchair base; `robmo-club-robot.local` | [Club robot](robots/club/README.md) |
| Personal | Jetson TX2, 14-inch circular Zagros base; `tx2.local` | [Personal robot](robots/personal/README.md) |

Start with the [robot directory](robots/README.md) for specs, photos, Blender
models, configuration references, and operating notes. Each robot has its own
record; dates and evidence distinguish measurements from estimates.

## Repository layout

```text
robots/
  club/
    README.md, specs.md, operations.md
    images/          original club photographs
    models/          club Blender scene, generator, GLB and previews
    docs/            club wiring and other robot-specific records
    config/          index of club configuration and unresolved values
  personal/
    README.md, specs.md, operations.md
    images/          original personal-robot photographs
    models/          home for personal models; no Blender scene yet
    docs/            TX2 calibration, geometry, sensor and repair records
    config/          index of the active personal runtime configuration
config/              active bind-mounted runtime files; indexed by robot above
model/               legacy ROS visualization/mesh workflow
ansible/             shared deployment tooling; inventory includes both robots
diagnostics/, odometry/, teensy/, touchscreen/, navigation/, bridge_policy/
                     implementation and service code
docs/shared/         shared reference designs with scope notes
docs/legacy/         archived documentation containing historical conflicts
```

Robot-specific photos, documents and model assets have one canonical copy under
`robots/`. Older photo/model paths are compatibility links, and moved Markdown
documents have short redirects. Runtime configuration and Compose mount paths
remain in place; this organization change does not deploy or restart a robot.

## Shared development

The stack uses ROS 2 Humble in Docker. See the
[software Compose file](docker-compose-ros.yml),
[hardware Compose file](docker-compose-ros-hardware.yml), and
[mock environment](mock/README.md).

```bash
./start_mock.sh up      # software and mock sensors/motors
./start_mock.sh down
```

The existing real-hardware Compose files contain personal TX2 settings. Consult
the selected robot's configuration index before deploying; the club robot does
not inherit the personal robot's calibration or footprint.

The [Ansible inventory](ansible/production) contains **both** robots. Use an
explicit target, for example `--limit robot` for club or `--limit tx2` for personal.
These are inventory names; check the target's operating notes for network access.
Physical control uses the [robot driver](.claude/skills/run-robomo-club-robot/SKILL.md).

## More documentation

- [Documentation index](docs/README.md)
- [Historical project guide](docs/legacy/project-guide.md): former README, preserved for reference
- [Legacy model workflow](model/README.md)
- [Contributor guidance](CLAUDE.md) and [robot-specific agent context](AGENTS.md)

Club project links: [forum](https://discourse.robomo.club/t/robomo-club-robot-project/82),
[website](http://robomo.club), [project board](https://github.com/frankjoshua/robomo-club-robot/projects/1).
