import bpy

obj = bpy.context.active_object
mesh = obj.data
print(len(mesh.vertices))

if "orig_index" not in mesh.attributes:
    attr = mesh.attributes.new("orig_index", type='INT', domain='POINT')
    
    for i, v in enumerate(mesh.vertices):
        attr.data[i].value = i
