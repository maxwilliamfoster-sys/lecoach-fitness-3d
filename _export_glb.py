import bpy, os
# Select only mesh objects (skip camera/light) and export the building as GLB
for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
out = r"C:\Users\maxwi\Desktop\LeCoach3D\lecoach_gym.glb"
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("EXPORT_OK", os.path.exists(out), os.path.getsize(out))
