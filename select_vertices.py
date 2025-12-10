import bpy
import bmesh
import mathutils

# --- Margin added to the bounding box ---
MARGIN = 0.1 # scale
SELECT_BY_BOX = True

# Get active object (must be a mesh)
obj = bpy.context.object
if obj is None or obj.type != 'MESH':
    raise RuntimeError("Active object must be a mesh.")

# Get BMesh from the object (must be in Edit Mode)
bm = bmesh.from_edit_mesh(obj.data)

# Collect world-space coordinates of currently selected vertices
selected_coords = [obj.matrix_world @ v.co for v in bm.verts if v.select]

if not selected_coords:
    print("No selected vertices. Select some vertices first to define the boundary.")
else:
    # Extract coordinate components
    xs = [p.x for p in selected_coords]
    ys = [p.y for p in selected_coords]
    zs = [p.z for p in selected_coords]

    # Compute bounding box with an optional margin

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    
    min_pt = mathutils.Vector((min_x, min_y, min_z))
    max_pt = mathutils.Vector((max_x, max_y, max_z))
    
    # Compute sphere center and radius based on the bounding box
    center = (min_pt + max_pt) / 2.0
    radius = max((p - center).length for p in selected_coords)        
    radius = radius * (1 + MARGIN)  # slightly expand the radius
    
    dx,dy,dz = (max_x-min_x)*MARGIN, (max_y-min_y)*MARGIN, (max_z-min_z)*MARGIN
    min_x, max_x = min_x-dx, max_x+dx
    min_y, max_y = min_y-dy, max_y+dy
    min_z, max_z = min_z-dz, max_z+dz

    # Select only vertices that fall inside the sphere region
    count_selected = 0
    for v in bm.verts:
        wco = obj.matrix_world @ v.co  # convert to world coordinates

        # Check by bounding box (optional, currently not used for selection)
        inside = (
            (min_x <= wco.x <= max_x) and
            (min_y <= wco.y <= max_y) and
            (min_z <= wco.z <= max_z)
        )
        if (SELECT_BY_BOX == False):
            # Check by sphere (this is the actual condition used)
            inside = (wco - center).length <= radius

        v.select = inside
        if inside:
            count_selected += 1

    # Update mesh after editing selection
    bmesh.update_edit_mesh(obj.data)

    # Print debugging information
    print("AABB boundary:")
    print(f"  min: ({min_x:.6f}, {min_y:.6f}, {min_z:.6f})")
    print(f"  max: ({max_x:.6f}, {max_y:.6f}, {max_z:.6f})")
    print(f"Sphere center: ({center.x:.6f}, {center.y:.6f}, {center.z:.6f})")
    print(f"Sphere radius: {radius:.6f}")
    print(f"{count_selected} vertices selected inside boundary.")

    # Save boundary parameters as reusable Python code in clipboard
    boundary_code = (
        f"min_x = {min_x}\n"
        f"max_x = {max_x}\n"
        f"min_y = {min_y}\n"
        f"max_y = {max_y}\n"
        f"min_z = {min_z}\n"
        f"max_z = {max_z}\n"
    )

    bpy.context.window_manager.clipboard = boundary_code
    print("Boundary parameter code copied to clipboard:")
    print(boundary_code)
