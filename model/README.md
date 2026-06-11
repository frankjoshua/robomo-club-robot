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
| `rsp.launch.py` | `robot_state_publisher` for the URDF — reads the plain all-fixed-joint URDF directly (no xacro, no joint_state_publisher), with the `ParameterValue(value_type=str)` wrap. |
| `serve_meshes.py` | Tiny CORS HTTP server for `meshes/` and the URDF itself (port 8100). |

## How it loads into the stack
`../docker-compose-model.yml` layers two things onto the ROS stack:
1. swaps `ros2_urdf` to plain `ros:humble-ros-base` running `robot_state_publisher` on the
   bind-mounted `robomo.urdf` (the published `frankjoshua/ros2-urdf` image is currently
   Jazzy-built, and a Jazzy node's Fast DDS wire format corrupts the Humble stack's discovery),
2. runs `model_meshes` to serve `meshes/` + the URDF over HTTP on `:8100`.

The URDF owns `base_link->laser_frame` at the real ~1.23 m scan height, so the mock lidar's own
laser TF is off by default in `../docker-compose-mock-hardware.yml`.

It's included in both `../start_mock.sh` and `../start_ros.sh`, so either `up` brings it up with
the rest — the model renders in Foxglove against the mock and the real robot alike.

### Why HTTP meshes (not `package://`)
`robot_state_publisher` only embeds the URDF text and publishes TF — it never resolves mesh
URIs; that's the viewer's job. The stack's bridge is **rosbridge**, which (unlike
`foxglove_bridge`) can't resolve `package://`, so the URDF points at
`http://localhost:8100/robomo.dae` and `model_meshes` serves it. Foxglove fetches it directly.

> Gotcha: the `http://` URL's colons make ROS 2 launch try to parse the URDF as YAML and crash
> with *"Unable to parse the value of parameter robot_description as yaml"* — hence the
> `ParameterValue(..., value_type=str)` wrap in `rsp.launch.py`.

## See it in Foxglove
1. `./start_mock.sh up` (or `./start_ros.sh up` against the real robot)
2. Foxglove → Open connection → **Rosbridge** → `ws://localhost:9090`
3. Layout → **Import from file** → [`../foxglove_layout.json`](../foxglove_layout.json) — done:
   3D panel with the robot model, `/scan`, `/map`, `/plan`, and click-to-publish nav2 goals
   (`/goal_pose`).

Or configure it by hand: add a **3D** panel → settings → **Custom layers** → **+** → **URDF** →
Source = **URL** `http://localhost:8100/robomo.urdf`, then set the display frame to `map` (or
`odom`) and add `/scan` / `/map`.

> Why URL rather than the `/robot_description` topic? rosbridge never replays a latched
> message to websocket clients that subscribe after `robot_state_publisher`'s single startup
> publish, so the topic source stays empty unless Foxglove happened to be subscribed when
> `ros2_urdf` (re)started. The URL works no matter when you connect.

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
