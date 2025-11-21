import bpy
import bmesh
import mathutils
import json

# Get current object in Edit Mode
obj = bpy.context.object
bm = bmesh.from_edit_mesh(obj.data)

# Collect selected vertices in world coordinates
coords = [obj.matrix_world @ v.co for v in bm.verts if v.select]

if not coords:
    print("No selected vertices.")
else:
    xs = [p.x for p in coords]
    ys = [p.y for p in coords]
    zs = [p.z for p in coords]

    # Bounding box
    min_pt = mathutils.Vector((min(xs), min(ys), min(zs)))
    max_pt = mathutils.Vector((max(xs), max(ys), max(zs)))
    center = (min_pt + max_pt) / 2.0

    # Mean position
    mean_pt = mathutils.Vector((
        sum(xs) / len(xs),
        sum(ys) / len(ys),
        sum(zs) / len(zs),
    ))

    # Radius: half of bounding-box diagonal (useful for sphere filter)
    bbox_diag = (max_pt - min_pt).length
    radius_bbox = bbox_diag * 0.5

    # Radius: max distance from center to any selected vertex
    radius_points = max((p - center).length for p in coords)

    # Build a dict that can be copy-pasted into your 3DGS filtering script
    region = {
        "bbox_min": " ".join(str(v) for v in [min_pt.x, min_pt.y, min_pt.z]),
        "bbox_max": " ".join(str(v) for v in [max_pt.x, max_pt.y, max_pt.z]),
        "center":  " ".join(str(v) for v in [center.x, center.y, center.z]),
        "mean":    " ".join(str(v) for v in [mean_pt.x, mean_pt.y, mean_pt.z]),
        "radius_bbox": float(radius_bbox),
        "radius_points": float(radius_points),
        "num_vertices": len(coords),
    }

    print("\n===== Region info for future 3DGS filtering (Python code) =====")
    print("region = " + json.dumps(region, indent=2))
    print("===============================================================\n")

    # (Optional) copy to clipboard for easy paste into another script
    bpy.context.window_manager.clipboard = "region = " + json.dumps(region, indent=2)
    print("Region info copied to clipboard.")

