import argparse
import numpy as np
from plyfile import PlyData, PlyElement


def filter_ply_by_sphere(input_ply, output_ply, bbox_min, bbox_max, radius_scale=1.3):
    print("[INFO] Loading:", input_ply)

    ply = PlyData.read(input_ply)
    if "vertex" not in ply:
        raise RuntimeError("Input PLY has no 'vertex' element. Not a valid 3DGS PLY.")

    vertex = ply["vertex"]

    # Extract xyz
    x = np.asarray(vertex["x"], dtype=np.float32)
    y = np.asarray(vertex["y"], dtype=np.float32)
    z = np.asarray(vertex["z"], dtype=np.float32)
    xyz = np.stack([x, y, z], axis=-1)

    bbox_min = np.array(bbox_min, dtype=np.float32)
    bbox_max = np.array(bbox_max, dtype=np.float32)

    # Sphere center = midpoint of bbox
    center = 0.5 * (bbox_min + bbox_max)

    # Base radius = distance to farthest bbox corner
    half_extents = 0.5 * (bbox_max - bbox_min)
    base_radius = np.linalg.norm(half_extents)

    radius = base_radius * radius_scale
    radius2 = radius * radius

    print(f"[INFO] Center       : {center}")
    print(f"[INFO] Base radius  : {base_radius}")
    print(f"[INFO] Scaled radius: {radius}")

    # Compute squared distance
    diff = xyz - center[None, :]
    dist2 = np.sum(diff * diff, axis=-1)

    mask = dist2 <= radius2
    total = xyz.shape[0]
    kept = int(mask.sum())

    print(f"[INFO] Total points: {total}")
    print(f"[INFO] Kept points : {kept}")

    if kept == 0:
        print("[WARN] No points remain after filtering!")

    # Apply mask
    filtered_vertex = vertex[mask]

    # Build new PlyData with same structure
    new_elements = []
    new_vertex_el = PlyElement.describe(filtered_vertex, "vertex")
    new_elements.append(new_vertex_el)

    # keep non-vertex elements if any
    for el in ply.elements:
        if el.name != "vertex":
            new_elements.append(el)

    new_ply = PlyData(new_elements, text=ply.text)
    new_ply.write(output_ply)

    print("[INFO] Saved filtered PLY →", output_ply)


def main():
    parser = argparse.ArgumentParser(description="Filter DreamGaussian PLY by spherical region.")
    parser.add_argument("--input_ply", type=str, required=True, help="Path to input 3DGS PLY file.")
    parser.add_argument("--output_ply", type=str, required=True, help="Path to save filtered PLY.")
    parser.add_argument("--bbox_min", type=float, nargs=3, required=True,
                        help="Bounding box min (x_min y_min z_min)")
    parser.add_argument("--bbox_max", type=float, nargs=3, required=True,
                        help="Bounding box max (x_max y_max z_max)")
    parser.add_argument("--radius_scale", type=float, default=1.3,
                        help="Scale factor for bounding-sphere radius (default: 1.3)")

    args = parser.parse_args()

    filter_ply_by_sphere(
        input_ply=args.input_ply,
        output_ply=args.output_ply,
        bbox_min=args.bbox_min,
        bbox_max=args.bbox_max,
        radius_scale=args.radius_scale
    )


if __name__ == "__main__":
    main()
