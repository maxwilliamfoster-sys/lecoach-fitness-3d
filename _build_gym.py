import bpy, bmesh, os, math
from mathutils import Quaternion

# ---------------- reset scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
col = bpy.data.collections.new('LeCoach')
scene.collection.children.link(col)

def M(name, rgba, rough=0.9, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = rgba  # workbench viewport colour
    return m

m_floor = M('Floor',      (0.11,0.11,0.12,1), 0.9)
m_wall  = M('WallExt',    (0.10,0.10,0.11,1), 0.9)
m_part  = M('Partition',  (0.14,0.14,0.15,1), 0.9)
m_blue  = M('Blue',       (0.03,0.11,0.55,1), 0.5)
m_white = M('WetWhite',   (0.90,0.90,0.90,1), 0.7)
m_wood  = M('WoodPlat',   (0.42,0.28,0.15,1), 0.6)
m_roof  = M('Roof',       (0.11,0.12,0.13,1), 0.6, 0.4)
m_steel = M('Steel',      (0.28,0.30,0.34,1), 0.5, 0.7)
m_txt   = M('Label',      (0.95,0.85,0.35,1), 0.5)

# ---------------- dims ----------------
W, D = 32.0, 13.0
X0, X1 = -W/2, W/2      # -16 .. 16  (right = +X)
Y0, Y1 = -D/2, D/2      # front(entrance) = -6.5 .. back = 6.5
EAVE, APEX = 3.8, 5.3
TE = 0.2                # exterior wall thickness
H  = 2.8               # interior partition height
TP = 0.15              # interior partition thickness

def box(name, sx, sy, sz, x, y, z, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x,y,z))
    o = bpy.context.active_object; o.name = name
    o.scale=(sx,sy,sz); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o

def poly(name, verts, m):
    me=bpy.data.meshes.new(name); ob=bpy.data.objects.new(name,me); col.objects.link(ob)
    bm=bmesh.new(); vs=[bm.verts.new(v) for v in verts]; bm.faces.new(vs); bm.to_mesh(me); bm.free()
    me.materials.append(m); return ob

def wallX(name, xa, xb, y, m, gaps=(), h=H, t=TP, z0=0):
    xa,xb=min(xa,xb),max(xa,xb)
    cuts=sorted((c-w/2,c+w/2) for c,w in gaps)
    segs=[]; cur=xa
    for a,b in cuts:
        if a>cur: segs.append((cur,a))
        cur=max(cur,b)
    if cur<xb: segs.append((cur,xb))
    for i,(a,b) in enumerate(segs):
        if b-a>0.01: box(f'{name}_{i}', b-a, t, h, (a+b)/2, y, z0+h/2, m)

def wallY(name, ya, yb, x, m, gaps=(), h=H, t=TP, z0=0):
    ya,yb=min(ya,yb),max(ya,yb)
    cuts=sorted((c-w/2,c+w/2) for c,w in gaps)
    segs=[]; cur=ya
    for a,b in cuts:
        if a>cur: segs.append((cur,a))
        cur=max(cur,b)
    if cur<yb: segs.append((cur,yb))
    for i,(a,b) in enumerate(segs):
        if b-a>0.01: box(f'{name}_{i}', t, b-a, h, x, (a+b)/2, z0+h/2, m)

def label(text, x, y, size=0.9):
    bpy.ops.object.text_add(location=(x,y,0.12))
    o=bpy.context.active_object; o.name='LBL_'+text.split()[0]
    o.data.body=text; o.data.size=size; o.data.align_x='CENTER'; o.data.align_y='CENTER'
    o.data.materials.append(m_txt)
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o

# ---------------- envelope ----------------
box('Floor', W, D, 0.1, 0, 0, -0.05, m_floor)
box('Wall_Front', W, TE, EAVE, 0, Y0, EAVE/2, m_wall)
box('Wall_Back',  W, TE, EAVE, 0, Y1, EAVE/2, m_wall)
for sx,nm in ((X0,'Gable_W'),(X1,'Gable_E')):
    poly(nm, [(sx,Y0,0),(sx,Y1,0),(sx,Y1,EAVE),(sx,0,APEX),(sx,Y0,EAVE)], m_wall)
poly('Roof_S', [(X0,Y0,EAVE),(X1,Y0,EAVE),(X1,0,APEX),(X0,0,APEX)], m_roof)
poly('Roof_N', [(X0,Y1,EAVE),(X1,Y1,EAVE),(X1,0,APEX),(X0,0,APEX)], m_roof)
box('Ridge', W, 0.18, 0.22, 0, 0, APEX-0.11, m_steel)
for x in (-12,-6,0,6,12): box(f'Tie_{x}', 0.14, D, 0.2, x, 0, EAVE, m_steel)

# ---------------- interior partitions ----------------
# LEFT block: changing (front) + leg room (back), west of x=-8
wallY('P_west', Y0, Y1, -8, m_part, gaps=[(-1.5,1.1),(3.5,1.3)])          # doors: toilets, leg room (from main)
wallX('P_toilet_leg', X0, -8, 0, m_part, gaps=[(-12,1.0)])                # toilets<->leg door
# CHANGING floor (white) + a couple shower stubs
box('WetFloor', 8, 6.5, 0.04, -12, -3.25, 0.02, m_white)
for i in range(3): box(f'Shower_{i}', 1.2, 1.2, 2.0, -15+ i*1.4, -5.6, 1.0, m_white)
# LEG room wood platform + plate wall accent
box('LegPlatform', 6.0, 4.0, 0.06, -12, 3.0, 0.03, m_wood)

# RECEPTION: small room front-centre-left  x[-8,-3] y[-6.5,-3]
wallX('P_recep_N', -8, -3, -3, m_part, gaps=[(-5.5,1.1)])                 # door to main room
wallY('P_recep_E', Y0, -3, -3, m_part, gaps=[])                          # solid east wall
box('ReceptionDesk', 2.4, 0.7, 1.0, -6.2, -4.0, 0.5, m_wood)
box('EntranceMark', 1.1, 0.05, EAVE, -5.5, Y0+0.06, EAVE/2, m_blue)      # blue entrance door mark

# RIGHT side: two offices + arm area + functional room (far right)
# main room east wall at x=5 (doors into office & arm), open corridor y[1.5..6.5]
wallY('P_mainE', Y0, 1.5, 5, m_part, gaps=[(-4.0,0.9),(-0.3,0.9)])
box('P_mainE_top', TP, 5.0, H, 5, 4.0, H/2, m_part)                      # keep upper closed except door
# actually leave a passage: cut a door in that top piece
# offices block x[5,9]; split into Office1(front) / Office2(back) / arm further right
wallX('P_off_div', 5, 7.5, -1.0, m_part, gaps=[(6.2,0.9)])               # office1 | office2
wallY('P_off_E', Y0, 3.5, 7.5, m_part, gaps=[(-4,0.9),(1.5,0.9)])        # offices | arm area
wallX('P_off_N', 5, 7.5, 3.5, m_part, gaps=[])                          # back of offices
# ARM area x[7.5,9]  y[-6.5,3.5]
wallY('P_arm_E', Y0, 3.5, 9, m_part, gaps=[(0,1.0)])                     # arm | functional door
wallX('P_arm_N', 7.5, 9, 3.5, m_part, gaps=[])
# FUNCTIONAL room x[9,16] full depth: separated from main-room corridor by wall at x=9 (y 3.5..6.5)
wallY('P_func_W', 3.5, Y1, 9, m_part, gaps=[(5.0,1.4)])                  # door from corridor
box('FuncFloor', 7, 13, 0.04, 12.5, 0, 0.02, m_floor)

# blue accent skirting along main-room key walls
for seg in [('sk1',-8,-3,-3),('sk2',-8,5,None)]:
    pass
box('Accent_recepwall', 5, 0.06, 0.25, -5.5, -3.0, 0.13, m_blue)
box('Accent_mainE', 0.06, 8, 0.25, 5, -2.5, 0.13, m_blue)

# ---------------- labels (top-plan) ----------------
label('RECEPTION', -6, -4.8, 0.55)
label('MAIN ROOM', -2, 2.5, 1.0)
label('TOILETS/SHOWERS', -12, -3.2, 0.6)
label('LEG ROOM', -12, 3.2, 0.8)
label('OFFICE', 6.2, -3.8, 0.45)
label('OFFICE', 6.2, 1.0, 0.45)
label('ARM', 8.25, -1, 0.45)
label('FUNCTIONAL ROOM', 12.5, 0, 0.8)

# ---------------- top-down plan render ----------------
roof_names=['Roof_S','Roof_N','Ridge','Tie_-12','Tie_-6','Tie_0','Tie_6','Tie_12']
for n in roof_names:
    o=col.objects.get(n)
    if o: o.hide_render=True

cam_data=bpy.data.cameras.new('PlanCam'); cam_data.type='ORTHO'; cam_data.ortho_scale=W+2
cam=bpy.data.objects.new('PlanCam',cam_data); scene.collection.objects.link(cam)
cam.location=(0,0,40); cam.rotation_euler=(0,0,0)
scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='FLAT'; scene.display.shading.color_type='MATERIAL'
scene.render.resolution_x=1600; scene.render.resolution_y=int(1600*(D+2)/(W+2))
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\PLAN.png"
bpy.ops.render.render(write_still=True)

# ---------------- export GLB (with roof) ----------------
for n in roof_names:
    o=col.objects.get(n)
    if o: o.hide_render=False
# remove text labels from export (they don't mesh-export cleanly / not wanted in 3D)
for o in list(col.objects):
    if o.name.startswith('LBL_'): bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb",
                          export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.blend")
print("BUILD_DONE objects:", len(col.objects))
