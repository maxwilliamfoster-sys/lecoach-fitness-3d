import bpy, bmesh
from mathutils import Vector, Matrix

SCALE = 1.5   # enlarge the whole building & everything uniformly (about origin)

# ---------------- reset ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'
col=bpy.data.collections.new('LeCoach'); scene.collection.children.link(col)

def M(n,rgba,r=0.9,me=0.0):
    m=bpy.data.materials.get(n) or bpy.data.materials.new(n); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=r; b.inputs['Metallic'].default_value=me
    m.diffuse_color=rgba; return m
m_floor=M('Floor',(0.12,0.12,0.13,1)); m_wall=M('WallExt',(0.13,0.13,0.14,1))
m_roof=M('Roof',(0.10,0.11,0.12,1),0.6,0.4); m_steel=M('Steel',(0.30,0.32,0.36,1),0.5,0.7)
m_blue=M('Blue',(0.03,0.11,0.55,1),0.5); m_txt=M('Label',(0.85,0.55,0.15,1),0.5)
m_garage=M('Garage',(0.55,0.56,0.58,1),0.5,0.35)

# ---- shell: 3 units x 13.35m = 40.05m wide x 23.77m deep ----
UNIT=13.35; W=3*UNIT; D=23.77
X0,X1=-W/2,W/2; Y0,Y1=-D/2,D/2          # front(entrance side)=Y0 ; back=Y1
EAVE,APEX=3.5,5.0; TE=0.2; H=3.0; TP=0.15
centers=[-UNIT,0.0,UNIT]; bounds=[-W/2,-UNIT/2,UNIT/2,W/2]
# front EXTENSION (protrudes outward beyond Y0)
EYF=Y0-5.0; EXL=X0; EXR=10.0; EH=3.0

def box(n,sx,sy,sz,x,y,z,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z))
    o=bpy.context.active_object; o.name=n; o.scale=(sx,sy,sz)
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o
def poly(n,verts,m):
    me=bpy.data.meshes.new(n); ob=bpy.data.objects.new(n,me); col.objects.link(ob)
    bm=bmesh.new(); vs=[bm.verts.new(v) for v in verts]; bm.faces.new(vs); bm.to_mesh(me); bm.free()
    me.materials.append(m); return ob
def wallX(n,xa,xb,y,m,gaps=(),h=H,t=TP):
    xa,xb=min(xa,xb),max(xa,xb); cuts=sorted((c-w/2,c+w/2) for c,w in gaps); segs=[];cur=xa
    for a,b in cuts:
        if a>cur: segs.append((cur,a))
        cur=max(cur,b)
    if cur<xb: segs.append((cur,xb))
    for i,(a,b) in enumerate(segs):
        if b-a>0.01: box(f'{n}_{i}',b-a,t,h,(a+b)/2,y,h/2,m)
def wallY(n,ya,yb,x,m,gaps=(),h=H,t=TP):
    ya,yb=min(ya,yb),max(ya,yb); cuts=sorted((c-w/2,c+w/2) for c,w in gaps); segs=[];cur=ya
    for a,b in cuts:
        if a>cur: segs.append((cur,a))
        cur=max(cur,b)
    if cur<yb: segs.append((cur,yb))
    for i,(a,b) in enumerate(segs):
        if b-a>0.01: box(f'{n}_{i}',t,b-a,h,x,(a+b)/2,h/2,m)
def label(txt,x,y,s=0.9):
    bpy.ops.object.text_add(location=(x,y,0.12)); o=bpy.context.active_object
    o.name='LBL_'+txt.split()[0]; o.data.body=txt; o.data.size=s
    o.data.align_x='CENTER'; o.data.align_y='CENTER'; o.data.materials.append(m_txt)
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o

# ---- envelope ----
box('Floor',W,D,0.1,0,0,-0.05,m_floor)
box('Wall_Left', TE,D,EAVE,X0,0,EAVE/2,m_wall)
box('Wall_Right',TE,D,EAVE,X1,0,EAVE/2,m_wall)
def gable(y):
    top=[]; xs=[X1,centers[2],bounds[2],centers[1],bounds[1],centers[0],X0]; zs=[EAVE,APEX,EAVE,APEX,EAVE,APEX,EAVE]
    for x,z in zip(xs,zs): top.append((x,y,z))
    return [(X0,y,0),(X1,y,0)]+top
poly('Wall_Back',gable(Y1),m_wall)
# FRONT facade: lower wall w/ passages to the extension + gable triangles above
wallX('Wall_FrontLow', X0, X1, Y0, m_wall, gaps=[(-15,1.2),(0.75,1.6),(7.5,2.0),(15,4.0)], h=EAVE, t=TE)
for i,cx in enumerate(centers):
    lx,rx=bounds[i],bounds[i+1]
    poly(f'Wall_FrontGab_{i}', [(lx,Y0,EAVE),(rx,Y0,EAVE),(cx,Y0,APEX)], m_wall)
# roof
for i,cx in enumerate(centers):
    lx,rx=bounds[i],bounds[i+1]
    poly(f'Roof_{i}_L',[(lx,Y0,EAVE),(lx,Y1,EAVE),(cx,Y1,APEX),(cx,Y0,APEX)],m_roof)
    poly(f'Roof_{i}_R',[(cx,Y0,APEX),(cx,Y1,APEX),(rx,Y1,EAVE),(rx,Y0,EAVE)],m_roof)
    box(f'Ridge_{i}',0.16,D,0.18,cx,0,APEX-0.1,m_steel)
for gy in (-8,0,8): box(f'Tie_{gy}',W,0.14,0.18,0,gy,EAVE-0.1,m_steel)
box('EntranceDoor',1.2,0.10,2.2,0.0,EYF-0.06,1.1,m_blue)          # on extension outer wall
# GARAGE / roller door in the functional-room front wall (faces car park) — 6 sectional panels
for i in range(6): box(f'GarageDoor_{i}',3.9,0.10,0.46,15.0,Y0-0.02,0.25+i*0.48,m_garage)
# CEILING FANS throughout the gym
def fan(x,y,z=3.2):
    box(f'FanRod_{x}_{y}',0.06,0.06,0.5,x,y,z+0.3,m_steel)
    box(f'FanHub_{x}_{y}',0.34,0.34,0.2,x,y,z,m_steel)
    box(f'FanBladeE_{x}_{y}',1.2,0.22,0.03,x+0.7,y,z-0.05,m_steel)
    box(f'FanBladeW_{x}_{y}',1.2,0.22,0.03,x-0.7,y,z-0.05,m_steel)
    box(f'FanBladeN_{x}_{y}',0.22,1.2,0.03,x,y+0.7,z-0.05,m_steel)
    box(f'FanBladeS_{x}_{y}',0.22,1.2,0.03,x,y-0.7,z-0.05,m_steel)
for fx,fy in [(-14,-4),(-6,-4),(-14,-9),(-6,-9),(0,-8),(8,-4),(15,-6),(15,0),(15,6),(-15,4),(-15,9)]:
    fan(fx,fy)

# ==================== INTERIOR (from user's design-mode walls) ====================
# y=0 partition: leg-room opening x[-18..-12]; back area re-SEALED (solid, no door)
wallX('Wall_y0a', X0, -18, 0.0, m_wall)
wallX('Wall_y0b', -12, 10, 0.0, m_wall)
wallY('Wall_xm10', 0.0, Y1, -10, m_wall)
# x=10 partition (functional room west): single opening at y[-6..-2]
wallY('Wall_x10a', Y0, -6, 10, m_wall)
wallY('Wall_x10b', -2, Y1, 10, m_wall)
# OFFICE 1 & 2 at the front of the main room: x[2..6] y[-11.885..-8], doors into main
wallY('Wall_Off_L', Y0, -8, 2, m_wall)
wallY('Wall_Off_M', Y0, -8, 4, m_wall)
wallY('Wall_Off_R', Y0, -8, 6, m_wall)
wallX('Wall_Off_N', 2, 6, -8, m_wall, gaps=[(3,0.9),(5,0.9)])

# ==================== FRONT EXTENSION (protruding OUTWARD) ====================
box('Floor_Ext', EXR-EXL, Y0-EYF, 0.1, (EXL+EXR)/2, (EYF+Y0)/2, -0.05, m_floor)
box('Ceil_Ext',  EXR-EXL, Y0-EYF, 0.12,(EXL+EXR)/2, (EYF+Y0)/2, EH+0.06, m_wall)   # flat roof
wallX('Wall_ExtFront', EXL, EXR, EYF, m_wall, gaps=[(0,1.6)], h=EH, t=TE)          # outer wall + entrance door
box('Wall_ExtLeft', TE, Y0-EYF, EH, EXL, (EYF+Y0)/2, EH/2, m_wall)
box('Wall_ExtRight',TE, Y0-EYF, EH, EXR, (EYF+Y0)/2, EH/2, m_wall)
# extension dividers: TOILETS/LOCKERS (left) | RECEPTION (mid) | right room
wallY('Wall_ExtDivL', EYF, Y0, -3.5, m_wall)   # lockers/toilets zone | reception (ext-right room removed -> reception x[-3.5,10])
# MALE + FEMALE toilets at the front of the toilets/lockers zone; rest = lockers
wallY('Wall_MFdiv', EYF, -14, -8,    m_wall)                             # male|female divider
wallY('Wall_FemL',  EYF, -14, -12.5, m_wall)                            # female left wall
wallX('Wall_ToiBack', -12.5, -3.5, -14, m_wall, gaps=[(-10,0.9),(-6,0.9)])  # WC back wall + doors

# ---- labels ----
label('LEG ROOM',-15,6,1.0); label('MAIN ROOM',-5,-4,1.1)
label('FUNCTIONAL ROOM',15,2,0.9); label('(sealed)',0,6,0.7)
label('RECEPTION',3,-13.8,0.6); label('LOCKERS',-16,-13.2,0.5)
label('FEMALE',-10.25,-15.4,0.4); label('MALE',-5.75,-15.4,0.4)
label('OFF1',3,-10,0.4); label('OFF2',5,-10,0.4)

# ---- top-down plan render (frames extension too) ----
hide=[o.name for o in col.objects if o.name.startswith(('Roof_','Ridge_','Tie_','Ceil_'))]
for n in hide:
    o=col.objects.get(n); o.hide_render=True
cam_d=bpy.data.cameras.new('Top'); cam_d.type='ORTHO'; cam_d.ortho_scale=W+3
cam=bpy.data.objects.new('Top',cam_d); scene.collection.objects.link(cam)
cam.location=Vector((0,(EYF+Y1)/2,50)); cam.rotation_euler=(0,0,0); scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.light='FLAT'; scene.display.shading.color_type='MATERIAL'
scene.render.resolution_x=1600; scene.render.resolution_y=int(1600*((Y1-EYF)+3)/(W+3))
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\PLAN.png"
bpy.ops.render.render(write_still=True)

# ---- export (enlarge everything 1.5x about origin) ----
for n in hide:
    o=col.objects.get(n); o.hide_render=False
for o in list(col.objects):
    if o.name.startswith('LBL_'): bpy.data.objects.remove(o,do_unlink=True)
S=Matrix.Scale(SCALE,4)
for o in bpy.data.objects:
    if o.type=='MESH': o.matrix_world = S @ o.matrix_world
bpy.context.view_layer.update()
for o in bpy.data.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb",
                          export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.blend")
print("EXT_DONE objects:",len(col.objects))
