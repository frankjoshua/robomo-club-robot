# Personal TX2 robot specifications

Compiled 2026-09-13 from owner confirmations and the September 12 calibration
and repair records. These are the latest recorded settings, not a new live audit.

| Item | Detail | Evidence / confidence |
| --- | --- | --- |
| Computer / host | NVIDIA Jetson TX2; `tx2.local` | Inspected deployment |
| Host / ROS | Ubuntu 18.04 / JetPack 4; ROS 2 Humble in Docker | Recorded deployment |
| Base | Zagros MAX-14 circular differential-drive chassis | Owner identification |
| Physical envelope | 0.3556 m (14 in) diameter; all components within base | Owner-confirmed 2026-09-12 |
| Navigation footprint | Radius 0.1778 m + 0.02 m padding | Configured Nav2 values |
| Wheel diameter | 0.1524 m (6 in) | Applied base specification / calibration |
| Effective turning track | 0.350 m | Rolling calibration; not a ruler measurement |
| Effective encoder scale | 262000 counts/revolution | Laser-referenced calibration; not a verified encoder part specification |
| Maximum RPM setting | 80 | Retained configuration, not a measured maximum |
| MCU / feedback | Teensy 4.0, dual LS7366R counters | Inspected firmware and diagnostics |
| Teensy power | USB only, no separate supply | Repeated owner confirmation |
| Motor controller | Sabertooth 2x32; Serial2 at 9600 baud | Recorded working setup; M2 left, M1 right |
| PID gains | 18.4 / 0 / 0 | Recorded readback; implementation-specific units |
| Lidar | YDLidar X4 at the front, above the camera | Inspected driver and owner mounting description |
| Camera | RealSense D435i, serial 943222072279 | Recorded driver audit |
| Odometry | Wheel translation plus bias-corrected RealSense gyro heading | Current implementation; this is not an extended Kalman filter |
| Display / touch | 800×480 HDMI display; USB touch `0eef:0005` | Touchscreen driver audit |
| USB hub rating | 4 A reported by owner | Rating only; aggregate consumption was not measured |
| Battery / full power topology | Not fully documented | Do not substitute the club's 24 V power diagram |

## Sensor geometry

Runtime transforms are defined in [config/tx2.urdf](../../config/tx2.urdf), with
positions in meters relative to `base_link`.

| Sensor | XYZ | Rotation | Evidence |
| --- | --- | --- | --- |
| Laser | (0.106, 0.008, 1.23) | yaw −0.065 rad | XY/yaw refined by motion; **height 1.23 m is inherited and unmeasured** |
| Camera | (0.105, 0.015, 0.398) | roll 0.0123, pitch 0.0125, yaw 0 rad | Height/tilt from floor fitting; XY estimated from mounting description |

The compact robot photos are not evidence for the inherited laser height. That
height still needs a physical measurement. Floor fitting measures camera height
and tilt, not its horizontal mounting offset.

## Validation limits

The [September 12 calibration](docs/calibration-2026-09-12.md) supersedes the
September 11 baseline of 310000 counts/rev and 0.300 m effective track. A short
held-out return compared 0.13272 m by laser with 0.13148 m odometry; this does not
establish room-scale accuracy. Low chair casters and camera blind spots remain
relevant; see [low obstacle coverage](docs/low-obstacles.md).

See the [config index](config/README.md) for authoritative runtime files,
[geometry audit](docs/tx2-sensor-geometry.md), and
[touchscreen implementation](../../touchscreen/README.md).
