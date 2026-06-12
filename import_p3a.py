import bpy
from math import radians
from struct import unpack


ROTATION_SCALE = radians(1 / 0x1000 * 90)
TransformRemap: dict[int, float] = {
    0x0040: 1 / 0x10,
    0x0080: 1 / 0x10,
    0x0100: 1 / 0x10,
    0x0008: ROTATION_SCALE,
    0x0010: ROTATION_SCALE,
    0x0020: ROTATION_SCALE,
    0x0200: 1 / 0x100,
    0x0400: 1 / 0x100,
    0x0800: 1 / 0x100,
}

def warning(messages: list[str] = [""], title: str = "Warning"):
    def draw(self, context):
        for message in messages:
            self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")


def insert_keyframe(obj, transform: int, frame: int, value: int) -> None:
    match transform:
        case 0x0008: #  "X Rot"
            obj.rotation_euler[0] = value * ROTATION_SCALE
            obj.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)
        case 0x0010: #  "Y Rot"
            obj.rotation_euler[1] = value * ROTATION_SCALE
            obj.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)
        case 0x0020: #  "Z Rot"
            obj.rotation_euler[2] = value * ROTATION_SCALE
            obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)
        case 0x0040: #  "X Trans"
            obj.location[0] = value / 0x10
            obj.keyframe_insert(data_path="location", index=0, frame=frame)
        case 0x0080: #  "Y Trans"
            obj.location[1] = value / 0x10
            obj.keyframe_insert(data_path="location", index=1, frame=frame)
        case 0x0100: #  "Z Trans"
            obj.location[2] = value / 0x10
            obj.keyframe_insert(data_path="location", index=2, frame=frame)
        case 0x0200: #  "X Scale"
            obj.scale[0] = value / 0x100
            obj.keyframe_insert(data_path="scale", index=0, frame=frame)
        case 0x0400: #  "Y Scale"
            obj.scale[1] = value / 0x100
            obj.keyframe_insert(data_path="scale", index=1, frame=frame)
        case 0x0800: #  "Z Scale"
            obj.scale[2] = value / 0x100
            obj.keyframe_insert(data_path="scale", index=2, frame=frame)


def do_bone_anim(file, bone, parent) -> None:
    transform_count, anim_size = unpack("2h", file.read(4))
    for _ in range(transform_count):
        transform_type, keyframe_count, transform_size = unpack("2HI", file.read(0x8))
        keyframes = [unpack("4h", file.read(0x8)) for _ in range(keyframe_count)]
        [insert_keyframe(bone, transform_type, frame_idx, value) for value, frame_idx, _, _ in keyframes]
        
        kps = parent.animation_data.action.fcurves[-1].keyframe_points
        for kf in range(len(keyframes)):
            print("pizza")
            kps[kf].interpolation = 'BEZIER'
            kps[kf].handle_left_type = 'FREE'
            kps[kf].handle_right_type = 'FREE'
            if kf == 0:
                prev_dt: float = 1
                next_dt: float = (keyframes[kf+1][1] - keyframes[kf][1]) / 3.0
                kps[kf].handle_left=(keyframes[kf][1] - prev_dt, (keyframes[kf][0]) * TransformRemap[transform_type])
                kps[kf].handle_right=(keyframes[kf][1] + next_dt, (keyframes[kf][0] + keyframes[kf][3] * next_dt) * TransformRemap[transform_type])
            elif kf == len(keyframes) - 1:
                prev_dt: float = (keyframes[kf][1] - keyframes[kf - 1][1]) / 3.0
                next_dt: float = 1
                kps[kf].handle_left=(keyframes[kf][1] - prev_dt, (keyframes[kf][0] - keyframes[kf][2] * prev_dt) * TransformRemap[transform_type])
                kps[kf].handle_right=(keyframes[kf][1] + next_dt, (keyframes[kf][0]) * TransformRemap[transform_type])
            else:
                prev_dt: float = (keyframes[kf][1] - keyframes[kf - 1][1]) / 3.0
                next_dt: float = (keyframes[kf+1][1] - keyframes[kf][1]) / 3.0
                kps[kf].handle_left=(keyframes[kf][1] - prev_dt, (keyframes[kf][0] - keyframes[kf][2] * prev_dt) * TransformRemap[transform_type])
                kps[kf].handle_right=(keyframes[kf][1] + next_dt, (keyframes[kf][0] + keyframes[kf][3] * next_dt) * TransformRemap[transform_type])
                

def import_anim(file, armature, missing_bones = None, bone_offset: int = 2) -> None:
    if missing_bones is None:
        missing_bones =  []
    skipped_bones = 0

    bone_count: int = unpack("i", file.read(4))[0]

    # Add bone keyframes
    file.seek(0xC, 1)
    for bone in range(bone_count):
        while bone + skipped_bones in missing_bones:
            skipped_bones += 1
        armature.pose.bones[bone + bone_offset + skipped_bones].rotation_mode = 'XYZ'
        do_bone_anim(file, armature.pose.bones[bone + bone_offset + skipped_bones], parent=armature)
    
    # Set start/end Frame
    bpy.data.scenes["Scene"].frame_start = 0
    bpy.data.scenes["Scene"].frame_end = int(max(curve.keyframe_points[-1].co[0] for curve in armature.animation_data.action.fcurves))


def execute(c, filepath: str, offset: int, missing: str) -> set[str]:
    obj = c.active_object
    if obj.type != 'ARMATURE':
        warning(["Active object is not an armature."])
        return {'CANCELLED'}
    if missing == '':
        missing_bones: list | None = None
    else:
        missing_bones: list | None = [int(x) for x in missing.split(",")]
    try:
        with open(filepath, "rb") as file:
            import_anim(
                file, 
                obj, 
                bone_offset=offset, 
                missing_bones=missing_bones
            )
    except:
        warning(["Import Error"])
        return {'CANCELLED'}
    return {'FINISHED'}
