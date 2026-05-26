import bpy, os

# Build the model first with build_robot.py (writes ~/robomo_blender_work/robomo.blend),
# then run this to export the body meshes into ../meshes (model/meshes/):
#   ~/blender/blender --background --python model/blender/export_meshes.py
WORK = os.path.expanduser("~/robomo_blender_work")
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "meshes"))
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, "robomo.blend"))

# select the robot body (all meshes except the floor)
bpy.ops.object.select_all(action='DESELECT')
body = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'floor']
for o in body:
    o.select_set(True)
bpy.context.view_layer.objects.active = body[0]
print(f"exporting {len(body)} body objects to {OUT}")

# Collada (.dae): Z-up, reliably oriented in ROS/RViz/Foxglove -> the URDF default
dae = os.path.join(OUT, "robomo.dae")
bpy.ops.wm.collada_export(filepath=dae, apply_modifiers=True, selected=True, triangulate=True)

# glTF binary (.glb): nicer PBR materials (Y-up per glTF spec) -> alternate
glb = os.path.join(OUT, "robomo.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True)

for f in (dae, glb):
    print(f"WROTE {f} {os.path.getsize(f)} bytes" if os.path.exists(f) else f"MISSING {f}")
print("DONE")
