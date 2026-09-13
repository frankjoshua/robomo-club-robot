# Club robot — photo-based Blender model

Open **club_robot.blend** in Blender. This is the **Robomo club Jetson Nano robot**
(`robmo-club-robot.local`), with its salvaged Little Rascal wheelchair base.
The eight original photographs are packed into the blend as `REFERENCE` images;
choose them in Blender's Image Editor. All modeled parts remain separate and
editable, organized into numbered collections under one robot root.

The scene includes the grey drive tires and four casters, blue foam front bumper,
painted plywood decks, round steel pipe and floor flange, four clear tray covers,
Nano plywood case, USB hub, prototype/GPS boards, clear power and Teensy boxes,
Sabertooth heatsinks, bus strips and wiring, Acer monitor with clear perimeter
guard, bezel webcam, K400-style keyboard, blue X4 lidar, white GL.iNet router,
and red emergency-stop button. The LCD is dark as photographed.

## Scale and evidence

This is a visual reconstruction, not a measured engineering model. Units are
meters, ground is Z=0, +X faces the monitor and blue bumper, and +Y is left.

| Dimension / feature | Model | Basis |
| --- | --- | --- |
| Overall width / length / height | about 0.50 / 0.91 / 1.22 m | Club overall-size paragraph in repository README; approximate |
| Drive tire diameter / track | 0.26 / 0.43 m | Estimated from photo proportions within that envelope |
| Caster diameter | 0.13 m | Photo estimate |
| Main deck height | 0.315 m | Photo estimate |
| Round mast diameter | 0.036 m | Photo estimate; photos show pipe, not extrusion |
| Monitor body | 0.46 wide × 0.29 high m | Photo estimate; exact Acer model unrecorded |
| Four trays | 0.27 long × 0.31 wide × 0.092 high m | Photo estimates |
| Top of blue lidar cap | 1.22 m | Scaled to documented approximate overall height |

The README's 0.15/0.1524 m wheel and 0.35 m track values conflict with the large
wheelchair wheels visible in these photos. They are not used to size this model.
The legacy Blender script also contains estimates (including an extrusion mast
and a different electronics layout) superseded here by the photos. The existing
1.23 m laser TF is not treated as a new measurement and is not changed.

The personal TX2's 14-inch circular Zagros base, its wheel dimensions, sensor
calibration, and USB-only Teensy power arrangement are not sources for this
model. No runtime URDF, navigation configuration, or deployed robot is modified.

Photo references: `robots/club/images/1000015852.jpg` (rear overview), `5853` (front overview),
`5854` (mast/power enclosure), `5855` and `5858` (lidar/router/top tray), `5856`
(rear drive electronics), `5857` (Teensy enclosure), `5859` (Nano case/trays).
Component identities follow the club bill of materials in the
[archived project guide](../../../docs/legacy/project-guide.md#hardware).
Hidden battery/motor shapes, component internals, exact cable routes and small
fastener details are representative. The front device visible above the monitor
is represented as a webcam; a personal-robot RealSense is not added.

## Files and rebuilding

- `club_robot.blend`: editable scene with packed reference photos and three cameras.
- `club_robot.glb`: portable robot-only export; separate from the legacy ROS meshes.
- `front.png`, `rear.png`, `electronics.png`: rendered previews.
- `blender/build_club_robot.py`: procedural source; edit `P` for main dimensions.

Preview: [front](front.png), [rear](rear.png), [electronics](electronics.png).
Legacy printable Jetson parts remain in [cad_files/](../../../cad_files/);
their fit and installation have not been verified against this reconstruction.

From the repository root (built with installed Blender 5.2.1):

```bash
blender --background --python robots/club/models/blender/build_club_robot.py
blender --background --python robots/club/models/blender/build_club_robot.py -- --no-render
```

Use `-- --samples 64` for cleaner previews. The GLB exporter may simplify
procedural materials; the Blender scene is the primary deliverable. The legacy
`build_robot.py`, `export_meshes.py`, and `model/meshes/robomo.*` remain their own
workflow and do not regenerate this photo-based scene.
