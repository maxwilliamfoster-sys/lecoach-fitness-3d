import bpy, bmesh, math
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
m_blue=M('Blue',(0.03,0.11,0.55,1),0.5)

# ---- REAL shell: 3 units x 13.35m = 40.05m wide x 23.77m deep ----
UNIT=13.35; W=3*UNIT; D=23.77
X0,X1=-W/2,W/2; Y0,Y1=-D/2,D/2      # front(entrance)=Y0 ; back=Y1
EAVE,APEX=3.5,5.0; TE=0.2
centers=[-UNIT,0.0,UNIT]                     # ridge x of each unit
bounds=[-W/2,-UNIT/2,UNIT/2,W/2]             # -20.025,-6.675,6.675,20.025

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

# floor
box('Floor',W,D,0.1,0,0,-0.05,m_floor)
# side walls (to eave)
box('Wall_Left', TE,D,EAVE,X0,0,EAVE/2,m_wall)
box('Wall_Right',TE,D,EAVE,X1,0,EAVE/2,m_wall)

# front & back gable walls following the M-roofline
def gable_profile(y):
    # bottom two corners then zig-zag top eave-apex-valley-apex... across X
    top=[]
    xs=[X1,centers[2],bounds[2],centers[1],bounds[1],centers[0],X0]
    zs=[EAVE,APEX,EAVE,APEX,EAVE,APEX,EAVE]
    for x,z in zip(xs,zs): top.append((x,y,z))
    return [(X0,y,0),(X1,y,0)]+top
poly('Wall_Front', gable_profile(Y0), m_wall)
poly('Wall_Back',  gable_profile(Y1), m_wall)

# roof: 2 slopes per unit (eave->ridge->eave)
for i,cx in enumerate(centers):
    lx,rx=bounds[i],bounds[i+1]
    poly(f'Roof_{i}_L',[(lx,Y0,EAVE),(lx,Y1,EAVE),(cx,Y1,APEX),(cx,Y0,APEX)],m_roof)
    poly(f'Roof_{i}_R',[(cx,Y0,APEX),(cx,Y1,APEX),(rx,Y1,EAVE),(rx,Y0,EAVE)],m_roof)
    box(f'Ridge_{i}',0.16,D,0.18,cx,0,APEX-0.1,m_steel)   # ridge beam
# a few tie beams across the width at eave level
for gy in (-8,0,8): box(f'Tie_{gy}',W,0.14,0.18,0,gy,EAVE-0.1,m_steel)

# entrance: roller shutter + personnel door on the front (centre unit)
box('RollerShutter',4.8,0.08,3.0,-2.0,Y0-0.05,1.5,m_steel)
box('EntranceDoor',1.1,0.08,2.2,2.8,Y0-0.05,1.1,m_blue)

# ---------------- renders ----------------
# perspective 3/4 exterior to show the shape
cam_d=bpy.data.cameras.new('Cam'); cam=bpy.data.objects.new('Cam',cam_d); scene.collection.objects.link(cam)
cam.location=Vector((34,-32,21)); d=Vector((0,0,2))-cam.location
cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.light='STUDIO'; scene.display.shading.color_type='MATERIAL'
scene.render.resolution_x=1500; scene.render.resolution_y=1000
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\SHELL.png"
bpy.ops.render.render(write_still=True)
# top-down footprint
cam2_d=bpy.data.cameras.new('Top'); cam2_d.type='ORTHO'; cam2_d.ortho_scale=W+3
cam2=bpy.data.objects.new('Top',cam2_d); scene.collection.objects.link(cam2)
cam2.location=Vector((0,0,50)); cam2.rotation_euler=(0,0,0); scene.camera=cam2
scene.render.resolution_y=int(1500*(D+3)/(W+3))
scene.render.filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\frames\PLAN.png"
bpy.ops.render.render(write_still=True)

# ---------------- export ----------------
for o in bpy.data.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb",
                          export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.blend")
print("SHELL_DONE objects:",len(col.objects),"footprint",round(W,2),"x",D,"eave",EAVE,"apex",APEX)
