import bpy, bmesh
from mathutils import Vector

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

# ---- REAL shell: 3 units x 13.35m = 40.05m wide x 23.77m deep ----
UNIT=13.35; W=3*UNIT; D=23.77
X0,X1=-W/2,W/2; Y0,Y1=-D/2,D/2      # front(entrance)=Y0 ; back=Y1
EAVE,APEX=3.5,5.0; TE=0.2
H=3.0; TP=0.15                       # interior partition height/thickness
centers=[-UNIT,0.0,UNIT]; bounds=[-W/2,-UNIT/2,UNIT/2,W/2]

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

# ---- envelope (floor, side walls, gable front/back, triple-pitch roof) ----
box('Floor',W,D,0.1,0,0,-0.05,m_floor)
box('Wall_Left', TE,D,EAVE,X0,0,EAVE/2,m_wall)
box('Wall_Right',TE,D,EAVE,X1,0,EAVE/2,m_wall)
def gable(y):
    top=[]; xs=[X1,centers[2],bounds[2],centers[1],bounds[1],centers[0],X0]; zs=[EAVE,APEX,EAVE,APEX,EAVE,APEX,EAVE]
    for x,z in zip(xs,zs): top.append((x,y,z))
    return [(X0,y,0),(X1,y,0)]+top
poly('Wall_Front',gable(Y0),m_wall); poly('Wall_Back',gable(Y1),m_wall)
for i,cx in enumerate(centers):
    lx,rx=bounds[i],bounds[i+1]
    poly(f'Roof_{i}_L',[(lx,Y0,EAVE),(lx,Y1,EAVE),(cx,Y1,APEX),(cx,Y0,APEX)],m_roof)
    poly(f'Roof_{i}_R',[(cx,Y0,APEX),(cx,Y1,APEX),(rx,Y1,EAVE),(rx,Y0,EAVE)],m_roof)
    box(f'Ridge_{i}',0.16,D,0.18,cx,0,APEX-0.1,m_steel)
for gy in (-8,0,8): box(f'Tie_{gy}',W,0.14,0.18,0,gy,EAVE-0.1,m_steel)
box('EntranceDoor',1.2,0.10,2.2,0.0,Y0-0.06,1.1,m_blue)
box('RollerShutter',4.8,0.08,3.0,-9.0,Y0-0.05,1.5,m_steel)

# ==================== ROOMS (from user's design-mode plan) ====================
# LEG ROOM  back-left  x[-20,-10]  y[0,back]
wallX('Wall_LegS', X0, -10, 0.0, m_wall, gaps=[(-14.0,1.6)])   # south wall, door to main
wallY('Wall_LegE', 0.0, Y1, -10, m_wall)                       # east wall (solid)
# FUNCTIONAL ROOM  right, full depth  x[10,20]  y[front,back]
wallY('Wall_FuncW', Y0, Y1, 10, m_wall, gaps=[(-4.0,1.6),(5.0,1.6)])  # west wall, two doors
# solid wall across the back-centre (former "delete this space") — NO doorway
wallX('Wall_MidBack', -10, 10, 0.0, m_wall)
# MAIN ROOM = the open FRONT span; back-centre is sealed off behind this wall.

# ---- labels for plan verification ----
label('LEG ROOM',-15,6,1.0); label('MAIN ROOM',0,-5,1.2)
label('FUNCTIONAL ROOM',15,0,0.95); label('(sealed)',0,6,0.7)

# ---- top-down plan render ----
hide=[o.name for o in col.objects if o.name.startswith(('Roof_','Ridge_','Tie_'))]
for n in hide:
    o=col.objects.get(n);  o.hide_render=True
cam_d=bpy.data.cameras.new('Top'); cam_d.type='ORTHO'; cam_d.ortho_scale=W+3
cam=bpy.data.objects.new('Top',cam_d); scene.collection.objects.link(cam)
cam.location=Vector((0,0,50)); cam.rotation_euler=(0,0,0); scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.light='FLAT'; scene.display.shading.color_type='MATERIAL'
scene.render.resolution_x=1600; scene.render.resolution_y=int(1600*(D+3)/(W+3))
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\PLAN.png"
bpy.ops.render.render(write_still=True)

# ---- export ----
for n in hide:
    o=col.objects.get(n); o.hide_render=False
for o in list(col.objects):
    if o.name.startswith('LBL_'): bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb",
                          export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.blend")
print("ROOMS_DONE objects:",len(col.objects))
