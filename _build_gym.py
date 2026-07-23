import bpy, bmesh, os

# ---------------- reset ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'
col=bpy.data.collections.new('LeCoach'); scene.collection.children.link(col)

def M(n,rgba,r=0.9,me=0.0):
    m=bpy.data.materials.get(n) or bpy.data.materials.new(n); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=r; b.inputs['Metallic'].default_value=me
    m.diffuse_color=rgba; return m
m_floor=M('Floor',(0.11,0.11,0.12,1)); m_wall=M('WallExt',(0.10,0.10,0.11,1))
m_part=M('Partition',(0.14,0.14,0.15,1)); m_blue=M('Blue',(0.03,0.11,0.55,1),0.5)
m_white=M('WetWhite',(0.90,0.90,0.90,1),0.7); m_wood=M('WoodPlat',(0.42,0.28,0.15,1),0.6)
m_ceil=M('Ceiling',(0.09,0.09,0.10,1),0.95); m_steel=M('Steel',(0.28,0.30,0.34,1),0.5,0.7)
m_txt=M('Label',(0.95,0.85,0.35,1),0.5)

# ---- REAL footprint: 3 units side-by-side = ~40m wide x 23.77m deep ----
UNIT=13.35; W=3*UNIT            # 40.05 wide (X, frontage)
D=23.77                        # deep (Y): front(entrance)=-D/2 .. back=+D/2
X0,X1=-W/2,W/2; Y0,Y1=-D/2,D/2
HGT=3.6; TE=0.2; H=3.0; TP=0.15
FRONT=Y0                       # entrance frontage (faces car park)

def box(n,sx,sy,sz,x,y,z,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z))
    o=bpy.context.active_object; o.name=n; o.scale=(sx,sy,sz)
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); return o
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

# ---- envelope (rectangle, flat ceiling ~eaves 3.5m) ----
box('Floor',W,D,0.1,0,0,-0.05,m_floor)
box('Ceiling',W,D,0.1,0,0,HGT+0.05,m_ceil)
box('Wall_Front',W,TE,HGT,0,Y0,HGT/2,m_wall)
box('Wall_Back', W,TE,HGT,0,Y1,HGT/2,m_wall)
box('Wall_Left', TE,D,HGT,X0,0,HGT/2,m_wall)
box('Wall_Right',TE,D,HGT,X1,0,HGT/2,m_wall)
# exposed tie beams (industrial) running front-to-back at the 3 unit lines
for x in (-UNIT,0,UNIT): box(f'Tie_{int(x)}',0.16,D,0.18,x,0,HGT-0.2,m_steel)

# ================= FRONT LOBBY STRIP (y: Y0 .. -6.5) =================
LB=-6.5
# TOILETS / SHOWERS / CHANGING  front-left
wallY('P_toil_E',Y0,LB,-12.5,m_part,gaps=[(-9.0,1.1)])
wallX('P_toil_N',X0,-12.5,LB,m_part,gaps=[])
box('WetFloor',7.5,(LB-Y0),0.04,-16.25,(Y0+LB)/2,0.02,m_white)
for i in range(4): box(f'Shower_{i}',1.2,1.2,2.0,-19.2+i*1.6,Y0+0.9,1.0,m_white)
# RECEPTION  front-centre (small, at entrance)
wallY('P_recep_W',Y0,-8.5,-3,m_part); wallY('P_recep_E',Y0,-8.5,3,m_part)
wallX('P_recep_N',-3,3,-8.5,m_part,gaps=[(0,1.3)])
box('ReceptionDesk',3.0,0.7,1.0,0,-9.6,0.5,m_wood)
box('EntranceMark',1.4,0.05,HGT,0,Y0+0.06,HGT/2,m_blue)
# OFFICES (two)  front-centre-right
wallY('P_off_W',Y0,LB,7,m_part); wallY('P_off_E',Y0,LB,13,m_part)
wallX('P_off_N',7,13,LB,m_part,gaps=[(10,1.0)])
wallX('P_off_div',7,13,-9.2,m_part,gaps=[(10,0.9)])
# ARM area  front-right
wallY('P_arm_E',Y0,LB,17,m_part,gaps=[(-9.0,0.9)])
wallX('P_arm_N',13,17,LB,m_part,gaps=[(15,0.9)])

# ================= DEEP GYM (y: -6.5 .. back) =================
# LEG ROOM back-left, deep
wallX('P_leg_S',X0,-9,2.0,m_part,gaps=[(-14.0,2.6)])
wallY('P_leg_E',2.0,Y1,-9,m_part,gaps=[(7.0,1.3)])
box('LegPlatform',10.0,8.0,0.06,-14.5,7.0,0.03,m_wood)
# FUNCTIONAL ROOM right side, deep (big)
wallY('P_func_W',LB,Y1,9,m_part,gaps=[(-2.0,1.4),(6.0,1.6)])
box('FuncFloor',11,18.27,0.04,14.5,(LB+Y1)/2,0.02,m_floor)
# blue accents
box('Accent_funcW',0.06,18.27,0.25,9,(LB+Y1)/2,0.13,m_blue)
box('Accent_legE',0.06,9.87,0.25,-9,7.0,0.13,m_blue)

# ================= labels (top plan) =================
label('TOILETS / SHOWERS',-16.25,-9.2,0.6); label('RECEPTION',0,-10.4,0.5)
label('OFFICE',10,-7.6,0.45); label('OFFICE',10,-10.6,0.45); label('ARM',15,-9,0.45)
label('LEG ROOM',-14.5,7.0,1.0); label('MAIN ROOM',0,-1.0,1.2); label('FUNCTIONAL ROOM',14.5,3,0.9)

# ================= top-down plan render =================
hide=['Ceiling','Tie_-13','Tie_0','Tie_13']
for n in hide:
    o=col.objects.get(n)
    if o: o.hide_render=True
cam_data=bpy.data.cameras.new('PlanCam'); cam_data.type='ORTHO'; cam_data.ortho_scale=W+3
cam=bpy.data.objects.new('PlanCam',cam_data); scene.collection.objects.link(cam)
cam.location=(0,0,50); cam.rotation_euler=(0,0,0); scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.light='FLAT'; scene.display.shading.color_type='MATERIAL'
scene.render.resolution_x=1600; scene.render.resolution_y=int(1600*(D+3)/(W+3))
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\PLAN.png"
bpy.ops.render.render(write_still=True)

# ================= export =================
for n in hide:
    o=col.objects.get(n)
    if o: o.hide_render=False
for o in list(col.objects):
    if o.name.startswith('LBL_'): bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb",
                          export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.blend")
print("BUILD_DONE objects:",len(col.objects),"footprint",round(W,2),"x",D)
