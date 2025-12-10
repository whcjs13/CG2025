import bpy
import math
from mathutils import Quaternion, Euler, Vector

# -----------------------------------
# Translation mode options (used only if USE_TRANSLATION = True)
# -----------------------------------
# Translation offsets for root bone location
offset_x = 0.0
offset_y = 0.0
offset_z = 0.0
USE_TRANSLATION = (offset_x != 0 or offset_y != 0 or offset_z != 0)

# -----------------------------------
# Rotation mode options (used only if USE_TRANSLATION = False)
# -----------------------------------
# Rotation offsets in degrees (around local X/Y/Z)
# e.g., rotate 10 degrees around Y axis
rot_deg_x = 0.0
rot_deg_y = 0.0
rot_deg_z = 0.0

# Convert to radians and build quaternion for rotation mode
rot_rad_x = math.radians(rot_deg_x)
rot_rad_y = math.radians(rot_deg_y)
rot_rad_z = math.radians(rot_deg_z)

offset_euler = Euler((rot_rad_x, rot_rad_y, rot_rad_z), 'XYZ')
offset_quat = offset_euler.to_quaternion()

# -----------------------------------
# Target armature / root bone
# -----------------------------------

arm = bpy.context.active_object
root_bone_name = "mixamorig:Hips"  # Mixamo root bone name

if arm is None or arm.type != 'ARMATURE':
    raise RuntimeError("Active object must be an Armature.")

if arm.animation_data is None or not arm.animation_data.nla_tracks:
    raise RuntimeError("Armature has no NLA tracks / strips.")

# -----------------------------------
# Find selected NLA strip
# -----------------------------------

sel_strip = None
for track in arm.animation_data.nla_tracks:
    for strip in track.strips:
        if strip.select:
            sel_strip = strip
            break
    if sel_strip:
        break

if sel_strip is None:
    raise RuntimeError("No selected NLA strip found. Select a strip in the NLA Editor.")

action = sel_strip.action
if action is None:
    raise RuntimeError("Selected strip has no Action.")

print(f"Editing Action: {action.name} (used by the selected NLA strip)")

# -----------------------------------
# TRANSLATION-ONLY MODE
# -----------------------------------
if USE_TRANSLATION:
    print("Applying TRANSLATION offsets only...")

    # Collect location fcurves (X/Y/Z) for the root bone
    loc_fcurves = {}

    for fcurve in action.fcurves:
        if fcurve.data_path == f'pose.bones["{root_bone_name}"].location':
            loc_fcurves[fcurve.array_index] = fcurve

    if len(loc_fcurves) != 3:
        raise RuntimeError("Could not find 3 location fcurves for the root bone.")

    fcurve_loc_x = loc_fcurves[0]
    fcurve_loc_y = loc_fcurves[1]
    fcurve_loc_z = loc_fcurves[2]

    # Apply constant offset to all keyframes (handles included)
    for key in fcurve_loc_x.keyframe_points:
        key.co[1] += offset_x
        key.handle_left.y += offset_x
        key.handle_right.y += offset_x
    for key in fcurve_loc_y.keyframe_points:
        key.co[1] += offset_y
        key.handle_left.y += offset_y
        key.handle_right.y += offset_y
    for key in fcurve_loc_z.keyframe_points:
        key.co[1] += offset_z
        key.handle_left.y += offset_z
        key.handle_right.y += offset_z

    print("Translation offsets applied to root location of the selected strip's action.")

# -----------------------------------
# ROTATION MODE (global rotation: rotation_quaternion + position)
# -----------------------------------
else:
    print("Applying GLOBAL ROTATION (rotation_quaternion + position)...")

    # Collect fcurves for location and rotation_quaternion
    loc_fcurves = {}
    rot_fcurves = {}

    for fcurve in action.fcurves:
        if fcurve.data_path == f'pose.bones["{root_bone_name}"].location':
            loc_fcurves[fcurve.array_index] = fcurve
        elif fcurve.data_path == f'pose.bones["{root_bone_name}"].rotation_quaternion':
            rot_fcurves[fcurve.array_index] = fcurve

    # Need 3 location curves (x,y,z) and 4 quaternion curves (w,x,y,z)
    if len(loc_fcurves) != 3:
        raise RuntimeError("Could not find 3 location fcurves for the root bone.")
    if len(rot_fcurves) != 4:
        raise RuntimeError("Could not find 4 rotation_quaternion fcurves for the root bone.")

    fcurve_loc_x = loc_fcurves[0]
    fcurve_loc_y = loc_fcurves[1]
    fcurve_loc_z = loc_fcurves[2]

    fcurve_rot_w = rot_fcurves[0]
    fcurve_rot_x = rot_fcurves[1]
    fcurve_rot_y = rot_fcurves[2]
    fcurve_rot_z = rot_fcurves[3]

    num_keys = len(fcurve_rot_w.keyframe_points)

    for i in range(num_keys):
        # ----- 1) Rotate rotation_quaternion -----
        kw = fcurve_rot_w.keyframe_points[i]
        kx = fcurve_rot_x.keyframe_points[i]
        ky = fcurve_rot_y.keyframe_points[i]
        kz = fcurve_rot_z.keyframe_points[i]

        q = Quaternion((kw.co[1], kx.co[1], ky.co[1], kz.co[1]))
        q_new = offset_quat @ q

        dw = q_new.w - kw.co[1]
        dx = q_new.x - kx.co[1]
        dy = q_new.y - ky.co[1]
        dz = q_new.z - kz.co[1]

        kw.co[1] += dw
        kw.handle_left.y += dw
        kw.handle_right.y += dw

        kx.co[1] += dx
        kx.handle_left.y += dx
        kx.handle_right.y += dx

        ky.co[1] += dy
        ky.handle_left.y += dy
        ky.handle_right.y += dy

        kz.co[1] += dz
        kz.handle_left.y += dz
        kz.handle_right.y += dz

        # ----- 2) Rotate position (location) by the same quaternion -----
        kx_loc = fcurve_loc_x.keyframe_points[i]
        ky_loc = fcurve_loc_y.keyframe_points[i]
        kz_loc = fcurve_loc_z.keyframe_points[i]

        p = Vector((kx_loc.co[1], ky_loc.co[1], kz_loc.co[1]))
        p_new = offset_quat @ p

        dx_pos = p_new.x - p.x
        dy_pos = p_new.y - p.y
        dz_pos = p_new.z - p.z

        kx_loc.co[1] += dx_pos
        kx_loc.handle_left.y += dx_pos
        kx_loc.handle_right.y += dx_pos

        ky_loc.co[1] += dy_pos
        ky_loc.handle_left.y += dy_pos
        ky_loc.handle_right.y += dy_pos

        kz_loc.co[1] += dz_pos
        kz_loc.handle_left.y += dz_pos
        kz_loc.handle_right.y += dz_pos

    print("Global rotation applied to root rotation_quaternion and location of the selected strip's action.")

print("Done.")
