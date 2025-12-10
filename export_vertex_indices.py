import bpy
import os

# === Settings: output path for the index file ===
# Change this to your desired save location
output_path = r"D:\temp\filtered_indices.txt"

obj = bpy.context.active_object
mesh = obj.data

# Check if the mesh has the 'orig_index' attribute created earlier
if "orig_index" not in mesh.attributes:
    raise RuntimeError("The mesh does not contain 'orig_index'. Make sure you ran the initialization script first.")

attr = mesh.attributes["orig_index"]

# Collect orig_index values for all currently remaining vertices
indices = []
for v in mesh.vertices:
    orig_idx = attr.data[v.index].value
    indices.append(orig_idx)

# Save to a text file (one index per line)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    for idx in indices:
        f.write(f"{idx}\n")

print(f"Saved {len(indices)} vertex indices to {output_path}.")
