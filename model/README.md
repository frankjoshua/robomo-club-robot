# Robot model (URDF + meshes)

A clean-stylized 3D model of the robomo.club robot — a wheelchair-base diff-drive bot with a
centered 3 ft extrusion mast, a 17" monitor "head" (VESA clamp), the YDLidar on top above the
monitor, a pole electronics shelf (IMU / GPS / WiFi router), batteries up front and the compute
in back. Built procedurally in Blender, exported to a mesh, and wrapped in a URDF so the robot
is visible in **Foxglove Studio** and RViz.

## Files
| Path | What |
|---|---|
| `blender/build_robot.py` | Procedural Blender model (the source of truth) + render of two preview angles. |
| `blender/export_meshes.py` | Exports the body to `meshes/robomo.dae` (+ `.glb`). |
| `meshes/robomo.dae` | Body mesh, Collada/Z-up — reliably oriented in Foxglove/RViz (the URDF default). |
| `meshes/robomo.glb` | Same body, glTF binary — nicer PBR materials (alternate). |
| `robomo.urdf` | Visual + TF model: root `base_link`, frames `laser_frame` / `camera_link` (+ optical) / `imu_link` / `gps_link` matching the live stack. |
| `rsp.launch.py` | `robot_state_publisher` for the URDF, with the `ParameterValue(value_type=str)` wrap. |
| `serve_meshes.py` | Tiny CORS HTTP server for `meshes/` (port 8100). |

## How it loads into the stack
`../docker-compose-model.yml` layers three things onto the ROS stack:
1. points `ros2_urdf`'s `robot_state_publisher` at `robomo.urdf` (bind-mount, no image rebuild),
2. runs `model_meshes` to serve `meshes/` over HTTP on `:8100`,
3. turns off the mock lidar's `base_link->laser_frame` TF (the URDF now owns it at ~1.23 m).

It's included in `../start_mock.sh`, so `./start_mock.sh up` brings it up with the rest.

### Why HTTP meshes (not `package://`)
`robot_state_publisher` only embeds the URDF text and publishes TF — it never resolves mesh
URIs; that's the viewer's job. The stack's bridge is **rosbridge**, which (unlike
`foxglove_bridge`) can't resolve `package://`, so the URDF points at
`http://localhost:8100/robomo.dae` and `model_meshes` serves it. Foxglove fetches it directly.

> Gotcha: the `http://` URL's colons make ROS 2 launch try to parse the URDF as YAML and crash
> with *"Unable to parse the value of parameter robot_description as yaml"* — hence the
> `ParameterValue(..., value_type=str)` wrap in `rsp.launch.py`.

## See it in Foxglove
1. `./start_mock.sh up`
2. Foxglove → Open connection → **Rosbridge** → `ws://localhost:9090`
3. Add a **3D** panel → settings → **Custom layers** → **+** → **URDF** → Source = Topic `/robot_description`
4. Set the display frame to `map` (or `odom`). Optionally add `/scan` and `/map`.

If the model looks flat or sideways, switch the `<mesh filename=...>` in `robomo.urdf` to
`robomo.glb` and recreate `ros2_urdf`.

## Regenerate the model
Needs Blender 4.2 (headless is fine). Edit `blender/build_robot.py` (all dimensions are in the
`P` dict at the top), then:
```bash
~/blender/blender --background --python model/blender/build_robot.py     # build + preview renders
~/blender/blender --background --python model/blender/export_meshes.py   # -> meshes/robomo.dae + .glb
docker compose ... up -d ros2_urdf                                       # or ./start_mock.sh up
```

## Status / next
This is the **visual + TF** model: the body (including the drive wheels) is a single mesh on
`base_link`. The **physics** pass — articulated wheel links, `<collision>`, computed
`<inertial>`, and Gazebo Classic sensor/diff-drive plugins — is the next step.
