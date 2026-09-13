"""Photo-based club/Nano robot, separate from the legacy ROS mesh and personal TX2.

blender --background --python robots/club/models/blender/build_club_robot.py
Pass -- --no-render to build only, or -- --samples 64 for cleaner previews.
All coordinates are meters; +X is the monitor/foam-bumper side, +Z is up.
"""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROBOT_DIR = Path(__file__).resolve().parents[2]
ROOT = ROBOT_DIR.parents[1]
OUT = ROBOT_DIR / "models"
P = dict(
    # Overall envelope from README; component dimensions estimated from photos.
    width=0.50, length=0.91, height=1.22,
    drive_radius=0.13, drive_width=0.07, drive_track=0.43,
    caster_radius=0.065, caster_width=0.04, caster_x=0.365, caster_y=0.185,
    deck_z=0.315, deck_length=0.56, deck_width=0.43,
    mast_x=0.075, mast_radius=0.018, mast_top=1.135,
    tray_x=-0.105, tray_length=0.27, tray_width=0.31, tray_height=0.092,
    tray_levels=(0.385, 0.565, 0.745, 0.925),
    monitor_width=0.46, monitor_height=0.29, monitor_z=0.985,
    top_shelf_z=1.115,
)


def material(name, color, metal=0.0, rough=0.45, transmission=0.0, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Transmission Weight'].default_value = transmission
    p.inputs['IOR'].default_value = 1.46
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def finish(o, name, mat, bevel=0.0):
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    CURRENT.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod = o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return o


def box(name, size, loc, mat, bevel=0.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, mat, bevel)


def cylinder(name, radius, depth, loc, mat, axis='Z', vertices=48):
    rotation = {'X': (0, math.pi/2, 0), 'Y': (math.pi/2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=loc, rotation=rotation)
    o = finish(bpy.context.object, name, mat, min(0.001, depth/5))
    for face in o.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return o


def wire(name, points, mat, radius=0.002, cyclic=False, smooth=True):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 10
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new('BEZIER' if smooth else 'POLY')
    if smooth:
        spline.bezier_points.add(len(points)-1)
        for p, co in zip(spline.bezier_points, points):
            p.co = co
            p.handle_left_type = p.handle_right_type = 'AUTO'
    else:
        spline.points.add(len(points)-1)
        for p, co in zip(spline.points, points):
            p.co = (*co, 1)
    spline.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, curve)
    CURRENT.objects.link(o)
    curve.materials.append(mat)
    return o


def rod(name, start, end, radius, mat):
    delta = Vector(end)-Vector(start)
    o = cylinder(name, radius, delta.length, (Vector(start)+Vector(end))/2, mat)
    o.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    return o


def label(name, text, loc, size, mat, facing='TOP'):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = text
    curve.size = size
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.extrude = 0.00003
    o = bpy.data.objects.new(name, curve)
    CURRENT.objects.link(o)
    o.location = loc
    if facing == 'FRONT':
        o.rotation_euler = (math.pi/2, 0, math.pi/2)
    elif facing == 'BACK':
        o.rotation_euler = (math.pi/2, 0, -math.pi/2)
    curve.materials.append(mat)
    return o


def rounded_loop(cx, cy, length, width, z, radius=0.02):
    pts = []
    for x, y, angle in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
        for n in range(9):
            a = math.radians(angle+n*90/8)
            pts.append((cx+x*(length/2-radius)+radius*math.cos(a),
                        cy+y*(width/2-radius)+radius*math.sin(a), z))
    return pts


def tray(name, z):
    x, l, w, h = P['tray_x'], P['tray_length'], P['tray_width'], P['tray_height']
    # A thin, tapered shell, open at the bottom like the inverted food containers.
    lower = rounded_loop(x, 0, l, w, z+0.01)
    upper = rounded_loop(x, 0, l-0.018, w-0.018, z+h)
    n = len(lower)
    verts = lower+upper
    faces = [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    faces.append(tuple(range(n, 2*n)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name+' clear cover', mesh)
    CURRENT.objects.link(o)
    mesh.materials.append(M['clear'])
    solid = o.modifiers.new('1.3 mm clear plastic', 'SOLIDIFY')
    solid.thickness = 0.0013
    for level in (z+0.008, z+0.015):
        wire(name+' molded lip', rounded_loop(x, 0, l+0.008, w+0.008, level), M['clear'], 0.0025, True, False)
    box(name+' shelf', (l-0.008, w-0.015, 0.004), (x, 0, z), M['wood'])
    box(name+' rear latch', (0.007, 0.065, 0.016), (x-l/2-0.003, 0, z+0.01), M['black'])
    for y in (-0.13, 0.13):
        cylinder(name+' shelf bolt', 0.0045, 0.003, (-0.01, y, z+0.004), M['steel'], vertices=6)


def board(name, loc, size=(0.08, 0.06, 0.003)):
    x, y, z = loc
    box(name, size, loc, M['pcb'], 0.0007)
    box(name+' IC', (size[0]*0.30, size[1]*0.35, 0.003), (x, y, z+0.003), M['black'], 0.0003)
    for side in (-1, 1):
        for i in range(10):
            cylinder(name+' plated contact', 0.0009, 0.001,
                     (x-size[0]*0.40+i*size[0]*0.08, y+side*size[1]*0.42, z+0.002), M['brass'], vertices=8)


def terminal(name, x, y, z, count=5):
    box(name, (0.023, count*0.010, 0.012), (x, y, z), M['black'])
    for i in range(count):
        yy = y+(i-(count-1)/2)*0.010
        box(name+' link', (0.018, 0.006, 0.002), (x, yy, z+0.007), M['steel'], 0.0004)
        for xx in (x-0.005, x+0.005):
            cylinder(name+' screw', 0.0024, 0.002, (xx, yy, z+0.009), M['steel'], vertices=12)


def build():
    global CURRENT, M
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    M = {
        'black': material('Black molded plastic', (0.018, 0.022, 0.027), rough=0.38),
        'steel': material('Zinc plated hardware', (0.46, 0.50, 0.54), 0.85, 0.27),
        'tube': material('Black powder coated steel', (0.025, 0.030, 0.037), 0.55, 0.3),
        'wood': material('Black painted plywood', (0.028, 0.030, 0.029), rough=0.7),
        'ply': material('Birch plywood edge / Nano case', (0.51, 0.31, 0.12), rough=0.65),
        'tire': material('Wheelchair grey rubber', (0.19, 0.21, 0.19), rough=0.88),
        'tread': material('Raised rubber tread', (0.23, 0.25, 0.23), rough=0.85),
        'clear': material('Clear polycarbonate', (0.94, 0.975, 1.0), rough=0.10, transmission=1),
        'white': material('Warm white plastic', (0.79, 0.80, 0.75), rough=0.34),
        'velcro': material('White hook and loop tape', (0.65, 0.65, 0.60), rough=0.95),
        'pcb': material('Green circuit board', (0.025, 0.16, 0.075), rough=0.55),
        'bluepcb': material('Teensy breakout blue', (0.015, 0.09, 0.23), rough=0.5),
        'blue': material('YDLidar X4 blue cap', (0.025, 0.09, 0.47), rough=0.38),
        'foam': material('Blue foam bumper', (0.015, 0.25, 0.53), rough=0.98),
        'red': material('Red switch and power wire', (0.56, 0.015, 0.020), rough=0.35),
        'yellow': material('Yellow cable', (0.67, 0.46, 0.015), rough=0.4),
        'green': material('Green wire / terminal', (0.025, 0.34, 0.11), rough=0.4),
        'pink': material('Pink printed PCB mount', (0.57, 0.105, 0.22), rough=0.6),
        'brass': material('Brass contacts', (0.60, 0.39, 0.10), 0.75, 0.3),
        'screen': material('Powered off Acer LCD', (0.012, 0.019, 0.023), 0.22, 0.17),
        'lcd': material('Blue wattmeter backlight', (0.006, 0.065, 0.95), rough=0.35, emission=1),
    }
    # Fine bump conveys painted plywood without relying on external textures.
    for key, scale, strength in [('wood', 180, 0.22), ('foam', 260, 0.35)]:
        nodes = M[key].node_tree.nodes
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = scale
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = strength
        bump.inputs['Distance'].default_value = 0.0006
        M[key].node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        M[key].node_tree.links.new(bump.outputs['Normal'], nodes.get('Principled BSDF').inputs['Normal'])

    CURRENT = collection('01 - Club wheelchair chassis')
    for y in (-0.175, 0.175):
        rod('Longitudinal wheelchair frame tube', (-0.35, y, 0.16), (0.35, y, 0.16), 0.014, M['tube'])
    for x in (-0.16, 0.18):
        rod('Frame crossmember', (x, -0.18, 0.18), (x, 0.18, 0.18), 0.014, M['tube'])
    box('Battery cradle', (0.34, 0.30, 0.022), (0.02, 0, 0.11), M['tube'])
    for y in (-0.077, 0.077):
        box('12 V sealed lead acid battery (concealed estimate)', (0.19, 0.135, 0.145), (0.03, y, 0.194), M['black'], 0.006)
        box('Battery retaining strap', (0.035, 0.139, 0.148), (0.03, y, 0.194), M['tube'])
        cylinder('24 V gearmotor', 0.036, 0.14, (-0.02, y*1.8, 0.20), M['steel'], 'X')
    box('Upper deck exposed plywood edge', (P['deck_length'], P['deck_width'], 0.012), (0.015, 0, P['deck_z']), M['ply'])
    box('Upper black deck', (P['deck_length']+0.002, P['deck_width']+0.002, 0.01), (0.015, 0, P['deck_z']+0.003), M['wood'])
    box('Rear low electronics deck', (0.30, 0.32, 0.010), (-0.25, 0, 0.182), M['wood'])
    box('Front hinged service cover', (0.235, 0.30, 0.011), (0.20, 0, 0.33), M['wood'])
    for y in (-0.10, 0.10):
        cylinder('Service cover hinge', 0.003, 0.045, (0.083, y, 0.337), M['steel'], 'Y')
    for x in (-0.22, 0.24):
        for y in (-0.18, 0.18):
            box('Deck velcro strip', (0.07, 0.015, 0.0015), (x, y, 0.325), M['velcro'], 0.0005)

    CURRENT = collection('02 - Drive wheels and four casters')
    for side in (-1, 1):
        y = side*P['drive_track']/2
        r, w = P['drive_radius'], P['drive_width']
        cylinder('Main drive tire', r-0.003, w, (0, y, r), M['tire'], 'Y', 96)
        cylinder('Black recessed drive hub', r*0.63, w+0.002, (0, y, r), M['black'], 'Y')
        cylinder('Drive hub metal center', 0.035, w+0.005, (0, y, r), M['tube'], 'Y')
        cylinder('Axle cap', 0.013, w+0.01, (0, y, r), M['steel'], 'Y', 12)
        for i in range(40):
            angle = i*math.tau/40
            for row in (-1, 0, 1):
                a = angle+row*0.025
                o = box('Wheel tread block', (0.013, 0.019, 0.005),
                        (0.1275*math.sin(a), y+row*0.021, r+0.1275*math.cos(a)), M['tread'], 0.001)
                o.rotation_euler[1] = a
        for i in range(6):
            a = i*math.tau/6
            cylinder('Wheel hub bolt', 0.004, 0.003, (0.05*math.sin(a), y+side*(w/2+0.003), r+0.05*math.cos(a)), M['steel'], 'Y', 6)
        for end in (-1, 1):
            x, yy, cr = end*P['caster_x'], side*P['caster_y'], P['caster_radius']
            rod('Angled caster outrigger', (end*0.18, side*0.175, 0.18), (x-end*0.015, yy, 0.16), 0.012, M['tube'])
            cylinder('Caster swivel', 0.020, 0.05, (x-end*0.015, yy, 0.15), M['tube'])
            cylinder('Caster swivel top bolt', 0.007, 0.004, (x-end*0.015, yy, 0.177), M['steel'], vertices=6)
            cylinder('Grey caster wheel', cr, P['caster_width'], (x, yy, cr), M['tire'], 'Y', 64)
            cylinder('Caster black hub', cr*0.72, 0.043, (x, yy, cr), M['black'], 'Y')
            for groove in (-0.012, -0.006, 0, 0.006, 0.012):
                pts = [(x+(cr+0.0003)*math.sin(a*math.tau/64), yy+groove, cr+(cr+0.0003)*math.cos(a*math.tau/64)) for a in range(64)]
                wire('Caster rolling rib', pts, M['tread'], 0.001, True, False)
            for s in (-1, 1):
                box('Caster fork cheek', (0.035, 0.006, 0.075), (x-0.008*end, yy+s*0.026, 0.10), M['tube'], 0.004)
            cylinder('Caster axle', 0.005, 0.065, (x, yy, cr), M['steel'], 'Y', 12)
    rod('Blue pool noodle front bumper', (0.427, -0.225, 0.205), (0.427, 0.225, 0.205), 0.027, M['foam'])
    for y in (-0.18, 0.18):
        rod('Front bumper bracket', (0.29, y, 0.17), (0.427, y, 0.205), 0.009, M['tube'])
        wire('Bumper zip tie', [(0.427+0.028*math.sin(a*math.tau/32), y, 0.205+0.028*math.cos(a*math.tau/32)) for a in range(32)], M['black'], 0.002, True, False)

    CURRENT = collection('03 - Steel pipe mast and shelf structure')
    mx = P['mast_x']
    cylinder('Brown flange mounting plate', 0.07, 0.01, (mx, 0, 0.334), M['ply'])
    cylinder('Steel pipe floor flange', 0.053, 0.011, (mx, 0, 0.344), M['tube'])
    cylinder('Round black steel mast', P['mast_radius'], P['mast_top']-0.35, (mx, 0, (P['mast_top']+0.35)/2), M['tube'])
    for i in range(4):
        a = i*math.pi/2+math.pi/4
        cylinder('Mast flange hex bolt', 0.005, 0.006, (mx+0.038*math.cos(a), 0.038*math.sin(a), 0.352), M['steel'], vertices=6)
    box('Vertical black plywood spine', (0.015, 0.20, 0.77), (0.005, 0, 0.735), M['wood'])
    for y in (-0.135, 0.135):
        rod('Threaded tray support rod', (-0.012, y, 0.36), (-0.012, y, 1.115), 0.003, M['steel'])
    for z in (0.60, 0.99):
        wire('Galvanized U bolt around pipe', [(0.005, -0.027, z), (0.075, -0.027, z), (0.104, 0, z), (0.075, 0.027, z), (0.005, 0.027, z)], M['steel'], 0.003)
    box('Top shelf plywood edge', (0.28, 0.34, 0.016), (-0.085, 0, P['top_shelf_z']), M['ply'])
    box('Top shelf black paint', (0.281, 0.341, 0.013), (-0.085, 0, P['top_shelf_z']+0.002), M['wood'])

    CURRENT = collection('04 - Four clear electronics trays')
    for i, z in enumerate(P['tray_levels']):
        tray(f'Tray {i+1:02d}', z)
        # Supporting angle bracket meets the spine.
        box('Tray support bracket', (0.13, 0.025, 0.008), (-0.06, 0, z-0.008), M['steel'])
    z = P['tray_levels'][0]
    box('Onboard 24 V battery charger', (0.15, 0.085, 0.045), (-0.12, 0.018, z+0.027), M['black'], 0.005)
    for i in range(12):
        box('Charger ventilation groove', (0.085, 0.002, 0.001), (-0.12, -0.025+i*0.007, z+0.050), M['steel'], 0)
    z = P['tray_levels'][1]
    box('Jetson Nano plywood case floor', (0.145, 0.12, 0.004), (-0.12, 0.035, z+0.008), M['ply'])
    box('Jetson Nano plywood case roof', (0.145, 0.12, 0.004), (-0.12, 0.035, z+0.069), M['ply'])
    for y in (-0.023, 0.093):
        box('Nano plywood case side', (0.145, 0.004, 0.058), (-0.12, y, z+0.039), M['ply'])
    # Rear wall leaves an actual open port aperture.
    for yy in (-0.011, 0.081):
        box('Nano case rear port surround', (0.004, 0.025, 0.058), (-0.190, yy, z+0.039), M['ply'])
    board('Jetson Nano carrier board', (-0.12, 0.035, z+0.020), (0.10, 0.08, 0.003))
    for yy in (0.014, 0.041):
        box('Jetson USB socket', (0.016, 0.016, 0.013), (-0.178, yy, z+0.03), M['steel'])
    for yy in (0.005, 0.065):
        box('Nano case velcro strap', (0.153, 0.013, 0.002), (-0.12, yy, z+0.073), M['velcro'])
    box('Nano power adapter', (0.10, 0.045, 0.023), (-0.12, -0.072, z+0.02), M['black'])
    z = P['tray_levels'][2]
    box('USB hub', (0.13, 0.043, 0.018), (-0.12, 0.025, z+0.016), M['black'], 0.004)
    label('USB hub label', 'j5create', (-0.12, 0.025, z+0.026), 0.011, M['white'])
    for yy in (-0.023, 0.002, 0.027, 0.052):
        box('USB socket blue insert', (0.005, 0.015, 0.007), (-0.052, yy, z+0.018), M['blue'])
    z = P['tray_levels'][3]
    box('Pink prototype board mount', (0.09, 0.09, 0.012), (-0.13, -0.065, z+0.013), M['pink'])
    board('Upper sensor prototype board', (-0.13, -0.065, z+0.026), (0.084, 0.075, 0.003))
    board('Pico IMU module representation', (-0.135, -0.063, z+0.034), (0.035, 0.025, 0.003))
    board('USB GPS board representation', (-0.14, 0.078, z+0.014), (0.045, 0.035, 0.003))
    box('GPS receiver shield', (0.023, 0.025, 0.005), (-0.14, 0.078, z+0.019), M['steel'])
    for level in P['tray_levels']:
        wire('Coiled peripheral USB cable', [(-0.018, 0.07, level+0.03), (-0.12, 0.11, level+0.035), (-0.21, 0.045, level+0.025), (-0.15, -0.015, level+0.028), (-0.07, 0.06, level+0.03), (-0.025, 0.085, level+0.05)], M['black'], 0.0023)

    CURRENT = collection('05 - Power distribution and Teensy enclosures')
    # Vertical clear-front power enclosure, on the front of the spine behind pipe.
    box('Power distribution enclosure back', (0.026, 0.29, 0.24), (0.032, 0, 0.49), M['white'])
    box('Power distribution plywood insert', (0.005, 0.27, 0.218), (0.049, 0, 0.49), M['ply'])
    for y in (-0.09, -0.025, 0.045):
        box('Vertical power bus strip', (0.012, 0.027, 0.12), (0.061, y, 0.515), M['black'])
        for i in range(9):
            cylinder('Bus strip terminal screw', 0.0028, 0.003, (0.069, y, 0.465+i*0.012), M['steel'], 'X', 12)
        wire('Vertical bus power lead', [(0.067, y, 0.565), (0.072, y-0.018, 0.56), (0.072, y-0.018, 0.43), (0.07, 0.08, 0.405)], M['red'], 0.0014)
    box('TOBSUN 5 V converter', (0.018, 0.09, 0.03), (0.067, 0.035, 0.407), M['steel'])
    box('5 V display bezel', (0.016, 0.04, 0.022), (0.067, -0.095, 0.422), M['black'])
    label('5 V voltage readout', '5.15', (0.077, -0.095, 0.422), 0.009, M['lcd'], 'FRONT')
    box('Power enclosure clear front', (0.0015, 0.294, 0.244), (0.083, 0, 0.49), M['clear'])
    for y in (-0.147, 0.147):
        box('Power enclosure clear side', (0.05, 0.0015, 0.244), (0.059, y, 0.49), M['clear'])
    for z in (0.368, 0.612):
        box('Power enclosure clear edge', (0.05, 0.294, 0.0015), (0.059, 0, z), M['clear'])
    for y in (-0.134, 0.134):
        for z in (0.382, 0.599):
            cylinder('Enclosure corner screw', 0.004, 0.004, (0.085, y, z), M['steel'], 'X')
    # Low side Teensy box from photos 5854 and 5857.
    tx, ty, tz = -0.085, -0.155, 0.347
    box('Teensy enclosure mounting ears', (0.19, 0.10, 0.007), (tx, ty, tz), M['white'])
    box('Teensy enclosure bottom', (0.16, 0.085, 0.014), (tx, ty, tz+0.011), M['white'])
    board('Teensy terminal breakout', (tx, ty, tz+0.025), (0.10, 0.058, 0.003))
    box('Teensy 4.0 module', (0.035, 0.018, 0.003), (tx, ty, tz+0.03), M['bluepcb'])
    for yy in (ty-0.023, ty+0.023):
        box('Green screw terminal row', (0.10, 0.007, 0.01), (tx, yy, tz+0.032), M['green'])
    for yy in (ty-0.0425, ty+0.0425):
        box('Teensy enclosure clear side', (0.16, 0.0015, 0.043), (tx, yy, tz+0.035), M['clear'])
    for xx in (tx-0.08, tx+0.08):
        box('Teensy enclosure clear end', (0.0015, 0.085, 0.043), (xx, ty, tz+0.035), M['clear'])
    box('Teensy clear lid', (0.163, 0.088, 0.002), (tx, ty, tz+0.057), M['clear'])
    for i, color in enumerate(('red', 'yellow', 'green', 'blue', 'white')):
        wire('Teensy breakout jumper', [(tx-0.04, ty-0.023+i*0.009, tz+0.035), (tx, ty, tz+0.05), (tx+0.035, ty+0.02-i*0.008, tz+0.036)], M[color], 0.0009)
    # Exposed low rear Sabertooth, bus strips and blue wattmeter.
    board('Sabertooth 2x32 motor driver', (-0.245, -0.055, 0.203), (0.09, 0.08, 0.004))
    for yy in (-0.096, -0.014):
        box('Sabertooth heat sink base', (0.10, 0.013, 0.008), (-0.245, yy, 0.21), M['steel'])
        for i in range(14):
            box('Sabertooth heat sink fin', (0.003, 0.022, 0.025), (-0.29+i*0.007, yy, 0.221), M['steel'], 0.0003)
    for xx in (-0.267, -0.235):
        cylinder('Sabertooth capacitor', 0.009, 0.022, (xx, -0.055, 0.218), M['black'])
        cylinder('Capacitor metal top', 0.0085, 0.001, (xx, -0.055, 0.230), M['steel'])
    terminal('24 V bus', -0.245, 0.095, 0.199, 4)
    terminal('Ground bus', -0.245, 0.035, 0.199, 4)
    for yy, text in ((0.125, '24V'), (0.062, 'GND')):
        box(text+' white tape', (0.035, 0.017, 0.001), (-0.285, yy, 0.188), M['velcro'], 0)
        label(text+' label', text, (-0.285, yy, 0.189), 0.010, M['black'])
    box('Wattmeter black bezel', (0.045, 0.085, 0.024), (-0.36, -0.07, 0.20), M['black'])
    box('Wattmeter blue LCD', (0.034, 0.067, 0.001), (-0.36, -0.07, 0.213), M['lcd'])
    label('Wattmeter display', '24.0 V', (-0.36, -0.07, 0.214), 0.008, M['black'])
    box('Remote motor kill switch', (0.06, 0.075, 0.029), (-0.353, 0.054, 0.204), M['black'])
    box('Amber terminal cover', (0.015, 0.07, 0.015), (-0.32, 0.054, 0.203), M['yellow'])

    CURRENT = collection('06 - Acer monitor, webcam and keyboard')
    monitor = bpy.data.objects.new('Acer monitor assembly (slight upward tilt)', None)
    CURRENT.objects.link(monitor)
    before = set(CURRENT.objects)
    box('Monitor rear VESA boss', (0.036, 0.11, 0.10), (0.098, 0, P['monitor_z']), M['black'])
    box('Acer monitor housing', (0.029, P['monitor_width'], P['monitor_height']), (0.13, 0, P['monitor_z']), M['black'], 0.006)
    box('Unlit LCD glass', (0.0015, 0.431, 0.255), (0.1455, 0, P['monitor_z']+0.004), M['screen'], 0.001)
    # Thin protective guard and rim visible in the photos.
    for yy in (-0.2305, 0.2305):
        box('Clear monitor guard side rail', (0.009, 0.003, 0.294), (0.15, yy, P['monitor_z']), M['clear'])
    for zz in (P['monitor_z']-0.146, P['monitor_z']+0.146):
        box('Clear monitor guard rim', (0.009, 0.46, 0.003), (0.15, 0, zz), M['clear'])
    label('Acer bezel brand', 'acer', (0.146, 0, P['monitor_z']-0.134), 0.008, M['steel'], 'FRONT')
    box('Webcam clip', (0.036, 0.023, 0.027), (0.132, 0, 1.139), M['black'])
    box('Top bezel USB webcam', (0.026, 0.068, 0.023), (0.144, 0, 1.159), M['black'], 0.010)
    cylinder('Webcam lens ring', 0.008, 0.002, (0.159, 0, 1.159), M['steel'], 'X')
    cylinder('Webcam lens', 0.0058, 0.003, (0.160, 0, 1.159), M['screen'], 'X')
    # Parent with preserved coordinates, then tilt around screen center.
    monitor.location = (0.13, 0, P['monitor_z'])
    bpy.context.view_layer.update()
    for o in set(CURRENT.objects)-before:
        o.parent = monitor
        o.matrix_parent_inverse = monitor.matrix_world.inverted()
    monitor.rotation_euler[1] = math.radians(-7)
    box('Keyboard side support', (0.35, 0.13, 0.008), (0.10, -0.19, 0.331), M['wood'])
    box('Logitech K400 keyboard', (0.35, 0.13, 0.017), (0.10, -0.19, 0.343), M['black'], 0.009)
    for row in range(5):
        for col in range(14):
            x = -0.06+col*0.016
            y = -0.235+row*0.021
            box('Keyboard key', (0.014, 0.017, 0.003), (x, y, 0.353), M['tube'], 0.0015)
            if row > 0:
                label('Key legend', 'QWERTYUIOPASDF'[col], (x, y, 0.355), 0.004, M['velcro'])
    box('Keyboard touchpad', (0.085, 0.089, 0.001), (0.216, -0.185, 0.353), M['tube'])
    box('Touchpad yellow accent', (0.073, 0.0015, 0.001), (0.216, -0.216, 0.354), M['yellow'], 0)
    cylinder('Keyboard yellow button', 0.004, 0.001, (0.253, -0.138, 0.354), M['yellow'])

    CURRENT = collection('07 - Blue X4 lidar, white router and E-stop')
    box('X4 lower mounting plate', (0.085, 0.090, 0.005), (-0.012, 0.018, 1.130), M['black'])
    for y in (-0.017, 0.053):
        cylinder('X4 standoff', 0.003, 0.032, (-0.03, y, 1.147), M['tube'])
    cylinder('X4 exposed motor', 0.014, 0.027, (-0.043, 0.018, 1.149), M['steel'])
    cylinder('X4 black scanner base', 0.038, 0.017, (-0.005, 0.018, 1.171), M['black'])
    cylinder('X4 blue rotating housing', 0.037, 0.035, (-0.005, 0.018, 1.1995), M['blue'], vertices=96)
    cylinder('X4 blue lid', 0.0375, 0.003, (-0.005, 0.018, 1.2185), M['blue'], vertices=96)
    box('X4 dark optical aperture', (0.002, 0.022, 0.014), (-0.042, 0.018, 1.197), M['screen'], 0.006)
    # Belt path exposed below the scanner cap.
    wire('X4 drive belt', [(-0.061, 0.018, 1.174), (-0.013, -0.021, 1.174), (0.031, 0.018, 1.174), (-0.013, 0.056, 1.174)], M['black'], 0.0015, True)
    rx, ry = -0.14, -0.062
    for y in (ry-0.035, ry+0.035):
        box('Router velcro feet', (0.08, 0.014, 0.005), (rx, y, 1.127), M['velcro'])
    box('White GL.iNet router', (0.093, 0.135, 0.036), (rx, ry, 1.147), M['white'], 0.013)
    box('Router grey front seam', (0.0015, 0.103, 0.002), (rx-0.047, ry, 1.145), M['steel'])
    for y in (ry-0.071, ry+0.071):
        box('Folded white router antenna', (0.09, 0.009, 0.031), (rx+0.005, y, 1.15), M['white'], 0.004)
    label('Router branding', 'GL.iNet', (rx, ry, 1.166), 0.007, M['tube'])
    cylinder('Emergency stop metal collar', 0.012, 0.023, (0.005, 0.123, 1.136), M['steel'])
    cylinder('Emergency stop red mushroom', 0.022, 0.009, (0.005, 0.123, 1.152), M['red'])
    label('Emergency stop top marking', 'STOP', (0.005, 0.123, 1.157), 0.008, M['white'])

    CURRENT = collection('08 - Visible power and USB harnesses')
    for i, color in enumerate(('red', 'black', 'yellow', 'white', 'blue')):
        y = 0.108+i*0.004
        wire('Mast service harness '+color, [(-0.21, 0.075, 0.205), (-0.11, y, 0.29), (0.00, y, 0.36), (0.015, y, 0.59), (0.012, y, 0.84), (0.015, y, 1.07), (-0.045, y-0.04, 1.13)], M[color], 0.0015 if i > 1 else 0.0022)
    for i, color in enumerate(('red', 'black', 'green', 'yellow')):
        wire('Rear motor deck lead '+color, [(-0.35, 0.07-i*0.025, 0.22), (-0.29, 0.08-i*0.02, 0.20), (-0.21, 0.13-i*0.03, 0.235), (-0.12, 0.10-i*0.025, 0.27), (-0.06, 0.10-i*0.025, 0.28)], M[color], 0.0025)
    wire('Teensy blue USB cable', [(-0.08, -0.16, 0.385), (-0.15, -0.18, 0.36), (-0.03, -0.15, 0.42), (-0.012, -0.14, 0.76), (-0.12, -0.01, 0.78)], M['blue'], 0.0022)
    wire('Monitor power cable', [(0.11, 0.12, 0.96), (0.05, 0.17, 0.88), (0.035, 0.145, 0.60), (0.03, 0.10, 0.45)], M['black'], 0.0025)
    wire('Keyboard cable', [(0.22, -0.12, 0.35), (0.28, 0.01, 0.345), (0.12, 0.14, 0.348), (0.04, 0.14, 0.52)], M['black'], 0.002)
    for z in (0.46, 0.70, 0.89, 1.04):
        box('Harness white zip tie', (0.022, 0.03, 0.004), (0.013, 0.117, z), M['velcro'], 0.001)

    # One root allows convenient placement while keeping every part editable.
    robot_collections = list(bpy.context.scene.collection.children)
    CURRENT = collection('00 - Robot root')
    root = bpy.data.objects.new('ROBOMO CLUB - Jetson Nano wheelchair robot', None)
    CURRENT.objects.link(root)
    root['identity'] = 'Club robot / robmo-club-robot.local / Jetson Nano; NOT personal tx2.local'
    root['scale_basis'] = 'README approximate 0.50 W x 0.91 L x 1.22 H m; component sizes photo estimates'
    root['photos'] = 'robots/club/images/1000015852.jpg through 1000015859.jpg'
    for c in robot_collections:
        for o in c.objects:
            if o.parent is None:
                o.parent = root
    return root


def stage(root):
    global CURRENT
    CURRENT = collection('90 - Studio (excluded from GLB)')
    floor = material('Studio warm grey', (0.20, 0.225, 0.24), rough=0.83)
    box('Studio floor', (200, 200, 0.04), (0, 0, -0.022), floor, 0)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.50, 0.60, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.35
    for name, loc, energy, size in [('Large key', (2, -3, 4), 350, 3), ('Soft fill', (-3, -1, 2.5), 250, 2.5), ('Rear strip', (-1, 3, 3), 450, 2)]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.shape, data.size = energy, 'DISK', size
        o = bpy.data.objects.new(name, data)
        CURRENT.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.6))-o.location).to_track_quat('-Z', 'Y').to_euler()
    cameras = []
    for name, loc, target, scale in [
        ('Front three quarter', (2.3, -2.6, 1.95), (0, 0, 0.62), 1.57),
        ('Rear electronics', (-2.6, 2.0, 1.8), (-0.025, 0, 0.64), 1.54),
        ('Rear equipment detail', (-1.7, -1.5, 1.65), (-0.045, 0, 0.83), 0.94),
    ]:
        data = bpy.data.cameras.new(name)
        data.type, data.ortho_scale = 'ORTHO', scale
        o = bpy.data.objects.new(name, data)
        CURRENT.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z', 'Y').to_euler()
        cameras.append(o)
    scene.camera = cameras[0]
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 8
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    # Open the .blend with a useful orbit view, material colors, and only root selected.
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.color_type = 'MATERIAL'
                area.spaces.active.region_3d.view_distance = 2.0
                area.spaces.active.region_3d.view_location = (0, 0, 0.62)
                area.spaces.active.region_3d.view_rotation = cameras[0].rotation_euler.to_quaternion()
    return cameras


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    root = build()
    cameras = stage(root)
    for path in sorted((ROBOT_DIR/'images').glob('100001585*.jpg')):
        img = bpy.data.images.load(str(path), check_existing=True)
        img.name = 'REFERENCE - '+path.name
        img.use_fake_user = True
        img.pack()
    notes = bpy.data.texts.new('READ ME - Club robot identity and dimensions')
    notes.write((OUT/'README.md').read_text() if (OUT/'README.md').exists() else __doc__)
    root['estimated_dimensions_m'] = str(P)
    bpy.context.scene['model_scope'] = 'Photo-based visual model; not a measured CAD or dynamics model.'
    # Export only robot geometry, including curves and labels converted in the export copy.
    bpy.ops.object.select_all(action='DESELECT')
    for o in root.children_recursive:
        o.select_set(True)
    root.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'club_robot.glb'), export_format='GLB',
                              use_selection=True, export_apply=True, export_extras=True)
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'club_robot.blend'), compress=True)
    if not args.no_render:
        for cam, filename in zip(cameras, ('front.png', 'rear.png', 'electronics.png')):
            bpy.context.scene.camera = cam
            bpy.context.scene.render.filepath = str(OUT/filename)
            bpy.ops.render.render(write_still=True)
    print('CLUB_ROBOT_BUILD_COMPLETE', OUT)


parser = argparse.ArgumentParser()
parser.add_argument('--no-render', action='store_true')
parser.add_argument('--samples', type=int, default=32)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if __name__ == '__main__':
    main()
