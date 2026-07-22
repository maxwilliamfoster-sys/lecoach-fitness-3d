import bpy, bmesh, os, math

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
    m.diffuse_color = rgba
    return m

m_floor = M('Floor',     (0.11,0.11,0.12,1), 0.9)
m_wall  = M('WallExt',   (0.10,0.10,0.11,1), 0.9)
m_part  = M('Partition', (0.14,0.14,0.15,1), 0.9)
m_blue  = M('Blue',      (0.03,0.11,0.55,1), 0.5)
m_white = M('WetWhite',  (0.90,0.90,0.90,1), 0.7)
m_wood  = M('WoodPlat',  (0.42,0.28,0.15,1), 0.6)
m_roof  = M('Roof',      (0.11,0.12,0.13,1), 0.6, 0.4)
m_steel = M('Steel',     (0.28,0.30,0.34,1), 0.5, 0.7)
m_txt   = M('Label',     (0.95,0.85,0.35,1), 0.5)

# ---------------- dims ----------------
W, D = 32.0, 13.0
X0, X1 = -W/2, W/2      # left(-16) .. right(+16)
Y0, Y1 = -D/2, D/2      # front/entrance(-6.5) .. back(+6.5)
EAVE, APEX = 3.8, 5.3
TE = 0.2
H  = 2.8
TP = 0.15

def box(name, sx, sy, sz, x, y, z, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x,y,z))
    o=bpy.context.active_object; o.name=name
    o.scale=(sx,sy,sz); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o

def poly(name, verts, m):
    me=bpy.data.meshes.new(name); ob=bpy.data.objects.new(name,me); col.objects.link(ob)
    bm=bmesh.new(); vs=[bm.verts.new(v) for v in verts]; bm.faces.new(vs); bm.to_mesh(me); bm.free()
    me.materials.append(m); return ob

def wallX(name, xa, xb, y, m, gaps=(), h=H, t=TP):
    xa,xb=min(xa,xb),max(xa,xb); cuts=sorted((c-w/2,c+w/2) for c,w in gaps)
    segs=[]; cur=xa
    for a,b in cuts:
        if a>cur: segs.append((cur,a))
        cur=max(cur,b)
    if cur<xb: segs.append((cur,xb))
    for i,(a,b) in enumerate(segs):
        if b-a>0.01: box(f'{name}_{i}', b-a, t, h, (a+b)/2, y, h/2, m)

def wallY(name, ya, yb, x, m, gaps=(), h=H, t=TP):
    ya,yb=min(ya,yb),max(ya,yb); cuts=sorted((c-w/2,c+w/2) for c,w in gaps)
    segs=[]; cur=ya
    for a,b in cuts:
        if a>cur: segs.append((cur,a))
        cur=max(cur,b)
    if cur<yb: segs.append((cur,yb))
    for i,(a,b) in enumerate(segs):
        if b-a>0.01: box(f'{name}_{i}', t, b-a, h, x, (a+b)/2, h/2, m)

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

# ---------------- rooms (per user's sketch) ----------------
# LEG ROOM  back-left, deep : x[-16,-5] y[0.5,6.5]  (wide opening to main = dashed)
wallX('P_leg_S', -16, -5, 0.5, m_part, gaps=[(-10.0,2.4)])
wallY('P_leg_E', 0.5, 6.5, -5, m_part, gaps=[(3.5,1.2)])
box('LegPlatform', 8.0, 4.5, 0.06, -11, 3.2, 0.03, m_wood)

# TOILETS/SHOWERS  front-left corner : x[-16,-10.5] y[-6.5,-0.5]
wallY('P_toil_E', -6.5, -0.5, -10.5, m_part, gaps=[(-2.0,1.0)])
wallX('P_toil_N', -16, -10.5, -0.5, m_part, gaps=[])
box('WetFloor', 5.5, 6.0, 0.04, -13.25, -3.5, 0.02, m_white)
for i in range(3): box(f'Shower_{i}', 1.1, 1.1, 2.0, -15.2+i*1.5, -5.7, 1.0, m_white)

# RECEPTION  front-centre small box : x[-2.5,2.5] y[-6.5,-3.5]
wallY('P_recep_W', -6.5, -3.5, -2.5, m_part, gaps=[])
wallY('P_recep_E', -6.5, -3.5,  2.5, m_part, gaps=[])
wallX('P_recep_N', -2.5, 2.5, -3.5, m_part, gaps=[(0,1.2)])
box('ReceptionDesk', 2.6, 0.7, 1.0, 0.0, -4.6, 0.5, m_wood)
box('EntranceMark', 1.2, 0.05, EAVE, 0.0, Y0+0.06, EAVE/2, m_blue)

# OFFICES (two) : x[3.5,7.5] y[-6.5,-2.5]  right of reception
wallY('P_off_W', -6.5, -2.5, 3.5, m_part, gaps=[])
wallX('P_off_N', 3.5, 7.5, -2.5, m_part, gaps=[(5.5,1.0)])
wallX('P_off_div', 3.5, 7.5, -4.5, m_part, gaps=[(5.5,0.9)])   # split into 2 offices
wallY('P_off_E', -6.5, -2.5, 7.5, m_part, gaps=[])

# ARM area : x[7.5,9.5] y[-6.5,-3]  right of offices
wallX('P_arm_N', 7.5, 9.5, -3.0, m_part, gaps=[(8.5,0.9)])

# FUNCTIONAL ROOM : far-right big block x[9.5,16] full depth
wallY('P_func_W', -6.5, 6.5, 9.5, m_part, gaps=[(-4.5,0.9),(2.5,1.5)])
box('FuncFloor', 6.5, 13, 0.04, 12.75, 0, 0.02, m_floor)

# blue accents
box('Accent_recepN', 5, 0.06, 0.25, 0, -3.5, 0.13, m_blue)
box('Accent_funcW', 0.06, 13, 0.25, 9.5, 0, 0.13, m_blue)

# ---------------- labels ----------------
label('LEG ROOM', -11, 3.4, 0.9)
label('MAIN ROOM', 1.5, 3.0, 1.1)
label('TOILETS / SHOWERS', -13.2, -3.4, 0.55)
label('RECEPTION', 0, -5.0, 0.45)
label('OFFICE', 5.5, -3.5, 0.4)
label('OFFICE', 5.5, -5.4, 0.4)
label('ARM', 8.5, -4.8, 0.4)
label('FUNCTIONAL ROOM', 12.75, 0, 0.85)

# ---------------- top-down plan render ----------------
roof_names=['Roof_S','Roof_N','Ridge','Tie_-12','Tie_-6','Tie_0','Tie_6','Tie_12']
for n in roof_names:
    o=col.objects.get(n)
    if o: o.hide_render=True
cam_data=bpy.data.cameras.new('PlanCam'); cam_data.type='ORTHO'; cam_data.ortho_scale=W+2
cam=bpy.data.objects.new('PlanCam',cam_data); scene.collection.objects.link(cam)
cam.location=(0,0,40); cam.rotation_euler=(0,0,0); scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='FLAT'; scene.display.shading.color_type='MATERIAL'
scene.render.resolution_x=1600; scene.render.resolution_y=int(1600*(D+2)/(W+2))
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\PLAN.png"
bpy.ops.render.render(write_still=True)

# ---------------- export GLB ----------------
for n in roof_names:
    o=col.objects.get(n)
    if o: o.hide_render=False
for o in list(col.objects):
    if o.name.startswith('LBL_'): bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb",
                          export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.blend")
print("BUILD_DONE objects:", len(col.objects))
