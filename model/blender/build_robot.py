import bpy, os, math

WORK = os.path.expanduser("~/robomo_blender_work")
os.makedirs(WORK, exist_ok=True)

# ---------------- estimated dimensions (METERS) - REFINE THESE ----------------
P = dict(
    base_l=0.62, base_w=0.50, base_h=0.12, base_cz=0.18,    # black drive platform
    dw_r=0.155, dw_w=0.10, track=0.56, dw_x=-0.05,          # drive wheels
    caster_r=0.06, caster_x=0.27, caster_y=0.18,            # front casters
    deck_l=0.46, deck_w=0.40, deck_t=0.02, deck_z=0.30,     # centered electronics deck
    pole_s=0.04, pole_base_z=0.31, pole_len=0.90,           # centered 3 ft mast (on deck)
    eshelf_z=0.58,                                          # pole shelf: imu/gps/router (under monitor)
    mon_w=0.39, mon_h=0.25, mon_t=0.035, mon_z=0.92, mon_x=0.11,  # 17" monitor, VESA clamp
    laser_z=1.20,                                           # lidar at pole top, above monitor
)

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for b in list(coll):
            if getattr(b, 'users', 0) == 0:
                try: coll.remove(b)
                except Exception: pass

def mat(name, color, metallic=0.0, rough=0.5, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m

def smooth(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
    except Exception: bpy.ops.object.shade_smooth()

def box(name, size, loc, m, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        bm = o.modifiers.new("bev", "BEVEL"); bm.width = bevel; bm.segments = 3
    o.data.materials.append(m); smooth(o); return o

def cyl(name, r, h, loc, m, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m); smooth(o); return o

clear()

M_base   = mat("base",   (0.018, 0.018, 0.02), 0.1, 0.5)
M_tire   = mat("tire",   (0.012, 0.012, 0.014), 0.0, 0.85)
M_hub    = mat("hub",    (0.25, 0.25, 0.27), 1.0, 0.30)
M_alu    = mat("alu",    (0.62, 0.63, 0.66), 1.0, 0.32)
M_deck   = mat("deck",   (0.02, 0.03, 0.05), 0.2, 0.12)
M_box    = mat("ebox",   (0.03, 0.03, 0.035), 0.3, 0.40)
M_batt   = mat("batt",   (0.06, 0.06, 0.07), 0.1, 0.55)
M_pcb    = mat("pcb",    (0.02, 0.15, 0.06), 0.2, 0.50)
M_lidar  = mat("lidar",  (0.02, 0.02, 0.02), 0.2, 0.40)
M_accent = mat("accent", (0.95, 0.35, 0.05), 0.3, 0.35)
M_lens   = mat("lens",   (0.02, 0.05, 0.10), 0.0, 0.05)
M_mon    = mat("monbody",(0.015, 0.015, 0.018), 0.2, 0.45)
M_screen = mat("screen", (0.01, 0.02, 0.04), 0.0, 0.20, emit=(0.0, 0.5, 0.7), emit_str=2.0)
M_eye    = mat("eye",    (0.0, 0.8, 1.0), 0.0, 0.20, emit=(0.1, 0.9, 1.0), emit_str=8.0)
M_floor  = mat("floor",  (0.035, 0.035, 0.04), 0.0, 0.22)

# ---- drive base + wheels + casters ----
box("base", (P['base_l'], P['base_w'], P['base_h']), (0, 0, P['base_cz']), M_base, bevel=0.02)
for s in (1, -1):
    cyl(f"tire{s}", P['dw_r'], P['dw_w'], (P['dw_x'], s*P['track']/2, P['dw_r']), M_tire, rot=(math.radians(90), 0, 0))
    cyl(f"hub{s}",  P['dw_r']*0.45, P['dw_w']*1.02, (P['dw_x'], s*P['track']/2, P['dw_r']), M_hub, rot=(math.radians(90), 0, 0))
for s in (1, -1):
    cyl(f"cwheel{s}", P['caster_r'], 0.03, (P['caster_x'], s*P['caster_y'], P['caster_r']), M_tire, rot=(math.radians(90), 0, 0))
    box(f"cfork{s}", (0.02, 0.05, 0.10), (P['caster_x'], s*P['caster_y'], P['caster_r']+0.06), M_hub, bevel=0.005)

# ---- centered electronics deck ----
dz = P['deck_z']; dtop = dz + P['deck_t']/2
for sx in (1, -1):
    for sy in (1, -1):
        cyl(f"stand{sx}_{sy}", 0.008, 0.06, (sx*P['deck_l']/2*0.85, sy*P['deck_w']/2*0.85, dz-0.03), M_hub)
box("deck", (P['deck_l'], P['deck_w'], P['deck_t']), (0, 0, dz), M_deck, bevel=0.005)

# batteries IN FRONT
for s in (1, -1):
    box(f"battery{s}", (0.13, 0.13, 0.15), (0.15, s*0.10, dtop+0.075), M_batt, bevel=0.006)
# electronics IN BACK (Jetson, motor driver, PCB)
box("jetson",    (0.12, 0.10, 0.05),  (-0.13, 0.08, dtop+0.025), M_box, bevel=0.006)
box("sabertooth",(0.10, 0.08, 0.045), (-0.14, -0.09, dtop+0.022), M_box, bevel=0.005)
box("pcb",       (0.09, 0.06, 0.012), (-0.05, -0.02, dtop+0.006), M_pcb, bevel=0.002)

# ---- Realsense on front edge, forward-facing ----
fx = P['base_l']/2
box("cam", (0.025, 0.09, 0.025), (fx-0.005, 0, 0.28), M_mon, bevel=0.004)
for y in (-0.025, 0.025):
    cyl(f"lens{y}", 0.009, 0.012, (fx+0.01, y, 0.28), M_lens, rot=(0, math.radians(90), 0))

# ---- centered pole (3 ft extrusion on deck) ----
pb = P['pole_base_z']; pt = pb + P['pole_len']
box("pole", (P['pole_s'], P['pole_s'], P['pole_len']), (0, 0, (pb+pt)/2), M_alu, bevel=0.003)
box("pole_foot", (0.10, 0.10, 0.025), (0, 0, pb+0.012), M_hub, bevel=0.004)

# ---- pole electronics shelf (under monitor): IMU, GPS, WiFi router ----
ez = P['eshelf_z']
box("eshelf", (0.10, 0.24, 0.015), (0.07, 0, ez), M_alu, bevel=0.004)
box("imu", (0.03, 0.03, 0.012), (0.05, 0.08, ez+0.014), M_pcb, bevel=0.002)
box("gps", (0.05, 0.05, 0.02), (0.07, -0.02, ez+0.02), M_box, bevel=0.003)
cyl("gps_patch", 0.02, 0.008, (0.07, -0.02, ez+0.034), M_hub)
box("router", (0.06, 0.11, 0.025), (0.08, 0.04, ez+0.022), M_box, bevel=0.004)
for ay, at in ((0.085, 18), (0.105, -10)):
    cyl(f"ant{ay}", 0.004, 0.11, (0.08, ay, ez+0.085), M_mon, rot=(math.radians(at), 0, 0), verts=12)

# ---- VESA clamp + 17" monitor + glowing face ----
mz, mx = P['mon_z'], P['mon_x']
box("vesa_clamp", (0.05, 0.07, 0.06), (0, 0, mz), M_hub, bevel=0.005)
box("vesa_arm",   (0.07, 0.06, 0.05), (0.05, 0, mz), M_hub, bevel=0.004)
box("monbody", (P['mon_t'], P['mon_w'], P['mon_h']), (mx, 0, mz), M_mon, bevel=0.006)
sx0 = mx + P['mon_t']/2
box("screen", (0.004, P['mon_w']*0.92, P['mon_h']*0.88), (sx0+0.002, 0, mz), M_screen)
for ey in (-0.085, 0.085):
    cyl(f"eye{ey}", 0.032, 0.006, (sx0+0.006, ey, mz+0.03), M_eye, rot=(0, math.radians(90), 0), verts=32)

# ---- lidar at pole top, above the monitor ----
lz = P['laser_z']
box("laser_shelf", (0.13, 0.13, 0.012), (0.03, 0, lz), M_alu, bevel=0.004)
cyl("lidar_base", 0.04, 0.028, (0.03, 0, lz+0.02), M_lidar)
cyl("lidar_ring", 0.041, 0.006, (0.03, 0, lz+0.034), M_accent)
cyl("lidar_spin", 0.036, 0.016, (0.03, 0, lz+0.045), M_lidar)

# ---- floor ----
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
fl = bpy.context.active_object; fl.name = "floor"; fl.data.materials.append(M_floor)

# ---- lights ----
scene = bpy.context.scene
sd = bpy.data.lights.new("sun", 'SUN'); sd.energy = 3.5; sd.angle = math.radians(4)
su = bpy.data.objects.new("sun", sd); su.rotation_euler = (math.radians(55), math.radians(12), math.radians(35))
scene.collection.objects.link(su)
def area(name, loc, rot, energy, size):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size
    o = bpy.data.objects.new(name, l); o.location = loc; o.rotation_euler = rot
    scene.collection.objects.link(o)
area("fill", (-2.2, -1.6, 1.6), (math.radians(60), 0, math.radians(-55)), 400, 3.5)
area("rim",  (-0.8, 2.4, 1.8),  (math.radians(65), 0, math.radians(190)), 700, 2.0)
world = bpy.data.worlds['World']; world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.013, 0.02, 1); bg.inputs[1].default_value = 1.0

# ---- render ----
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
scene.cycles.samples = 64; scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True
try: scene.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
try: scene.view_settings.view_transform = 'AgX'
except Exception: pass

tgt = bpy.data.objects.new("tgt", None); scene.collection.objects.link(tgt)
camd = bpy.data.cameras.new("Camera"); cam = bpy.data.objects.new("Camera", camd)
scene.collection.objects.link(cam); scene.camera = cam
con = cam.constraints.new('TRACK_TO'); con.target = tgt
con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'

def render(name, cam_loc, tgt_loc, res=(1200, 950), lens=40):
    import time
    cam.location = cam_loc; tgt.location = tgt_loc; camd.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(WORK, name)
    t0 = time.time(); bpy.ops.render.render(write_still=True)
    print(f"WROTE {name} {res} in {time.time()-t0:.1f}s")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "robomo.blend"))
render("hero_34.png",   (2.3, -2.1, 1.00), (0, 0, 0.62), res=(1200, 950),  lens=40)
render("front_face.png",(2.9, -0.5, 1.05), (0, 0, 0.85), res=(950, 1180), lens=52)
print("DONE")
