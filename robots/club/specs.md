# Club robot specifications

Compiled 2026-09-13 from the club photographs, existing project documentation,
and the club Blender reconstruction. No new live hardware measurements were
performed for this organization pass.

| Item | Detail | Evidence / confidence |
| --- | --- | --- |
| Computer | NVIDIA Jetson Nano; arm64 | Club documentation and photo identification |
| Host | `robmo-club-robot.local` | Existing club access documentation |
| Software | ROS 2 Humble in Docker; Ubuntu 18.04 / L4T host documented | Historical deployment record; versions not rechecked |
| Chassis | Salvaged Little Rascal power-wheelchair base | Club documentation and photographs |
| Overall size | Approximately 0.50 m wide × 0.91 m long × 1.22 m high | Historical approximate envelope; used to scale the model |
| Drive wheel diameter / track | Not verified | Model uses 0.26 / 0.43 m as photo estimates only |
| Motor controller | Sabertooth 2x32 | Club bill of materials / wiring documentation |
| MCU and encoders | Teensy 4.0 and dual LS7366R counter board documented | Installed calibration and encoder part numbers need verification |
| Main battery arrangement | Two 12 V lead-acid batteries in series, 24 V system documented | Club power diagram; not a personal-robot specification |
| Teensy power | Separate 5 V bus-strip feed documented; USB described as data-only | Historical club wiring; verify against the physical assembly before rewiring |
| Lidar | YDLidar X4 on mast | Photos and bill of materials; precise transform unmeasured |
| Display / input | Acer monitor, wireless keyboard/touchpad | Photos; exact monitor model unrecorded |
| Camera | Bezel webcam visible | A D435i appears in older mixed documentation but installation on this robot is unverified |
| GPS / separate IMU | u-blox GPS documented; Pico IMU listed as work in progress | Historical BOM; current operation unverified |
| Network | GL.iNet router, SSID `ROBOMO-ROBOT-5G` | Club access documentation |

## Source material and unresolved values

Use the [photos](images/README.md), [model evidence table](models/README.md),
and [club wiring diagram](docs/wiring-diagram.html). The
[archived project guide](../../docs/legacy/project-guide.md#hardware) retains the
full historical bill of materials and power description.

The former README mixed the personal TX2's small-wheel calibration with the
club's wheelchair base. Values such as 0.1524 m wheel diameter, 262000 counts/rev,
and the 14-inch footprint are **personal robot values** and are not verified for
this robot. A measured club footprint, wheel calibration, sensor mounting
transforms, and installed camera inventory are still needed. The legacy ROS mesh
also differs from the current photos; keep its visual dimensions separate from
measured drivetrain parameters.
