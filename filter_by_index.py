"""
Filter a PLY file by vertex-like indices.

Usage:
    python filter_by_index.py input.ply indices.txt output.ply
"""

import sys
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement


def load_indices(indices_path):
    """Load integer indices from a text file (one index per line)."""
    indices = []
    with open(indices_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                idx = int(line)
                indices.append(idx)
            except ValueError:
                print(f"Warning: skip non-integer line: {line!r}")
    return indices


def pick_point_element(ply: PlyData):
    """
    Pick the element that represents point data (vertices/gaussians).
    Priority:
        1) element named 'vertex' if exists
        2) otherwise: first element that is not 'face'
    """
    element_names = [e.name for e in ply.elements]
    print("PLY elements:", element_names)

    # 1) Prefer 'vertex' if it exists
    for e in ply.elements:
        if e.name == "vertex":
            print("Using element 'vertex' as point element.")
            return e

    # 2) Fallback: pick first non-face element
    candidates = [e for e in ply.elements if e.name != "face"]
    if not candidates:
        raise RuntimeError("Could not find a suitable point element (no 'vertex' and no non-face elements).")

    chosen = candidates[0]
    print(f"No 'vertex' element found. Using element '{chosen.name}' as point element.")
    return chosen


def filter_ply_vertices(input_ply, indices_txt, output_ply):
    """Filter vertices/points in a PLY file, keeping only those whose index is in indices_txt."""
    input_ply = Path(input_ply)
    indices_txt = Path(indices_txt)
    output_ply = Path(output_ply)

    if not input_ply.exists():
        raise FileNotFoundError(f"Input PLY not found: {input_ply}")
    if not indices_txt.exists():
        raise FileNotFoundError(f"Indices file not found: {indices_txt}")

    # Load indices
    indices = load_indices(indices_txt)
    if not indices:
        raise RuntimeError("No valid indices loaded from indices.txt.")

    # Remove duplicates and sort (for stable behavior)
    unique_indices = sorted(set(indices))

    print(f"Loaded {len(indices)} indices ({len(unique_indices)} unique).")

    # Load PLY
    ply = PlyData.read(str(input_ply))

    # Pick element which behaves like "vertex"
    point_elem = pick_point_element(ply)
    point_data = point_elem.data  # numpy structured array
    num_points = len(point_data)

    print(f"Original point count ({point_elem.name}): {num_points}")

    # Make a boolean mask with True for points we want to keep
    mask = np.zeros(num_points, dtype=bool)
    out_of_range = 0
    for idx in unique_indices:
        if 0 <= idx < num_points:
            mask[idx] = True
        else:
            out_of_range += 1

    if out_of_range > 0:
        print(f"Warning: {out_of_range} indices were out of range and ignored.")

    kept_point_data = point_data[mask]
    kept_count = len(kept_point_data)

    if kept_count == 0:
        raise RuntimeError("No points left after filtering. Check indices.txt.")

    print(f"Filtered point count: {kept_count}")

    # Create new point element with the same dtype and name
    new_point_elem = PlyElement.describe(kept_point_data, point_elem.name)

    # Option 1: Only keep this point element (for 3DGS-style point clouds)
    new_elements = [new_point_elem]

    # If you want to keep faces or other elements, you could append them here,
    # but then you would need to remap indices in 'face' elements as well.
    # For 3D Gaussian Splatting PLYs (point clouds), there is usually no 'face'.

    new_ply = PlyData(
        new_elements,
        text=ply.text  # keep same text/binary mode as original
    )

    # Copy comments and obj_info if any
    new_ply.comments = list(ply.comments)
    new_ply.obj_info = list(ply.obj_info)

    # Write filtered PLY
    output_ply.parent.mkdir(parents=True, exist_ok=True)
    new_ply.write(str(output_ply))

    print(f"Filtered PLY written to: {output_ply}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python filter_by_index.py input.ply indices.txt output.ply")
        sys.exit(1)

    input_ply = sys.argv[1]
    indices_txt = sys.argv[2]
    output_ply = sys.argv[3]

    filter_ply_vertices(input_ply, indices_txt, output_ply)


if __name__ == "__main__":
    main()
