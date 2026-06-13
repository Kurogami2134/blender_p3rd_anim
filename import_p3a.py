import bpy
from .shared import ROTATION_TRANS, SCALE_TRANS, LOCATION_TRANS
from struct import unpack


TransformValues: dict[int, float] = {
    0x0040: LOCATION_TRANS,
    0x0080: LOCATION_TRANS,
    0x0100: LOCATION_TRANS,
    0x0008: ROTATION_TRANS,
    0x0010: ROTATION_TRANS,
    0x0020: ROTATION_TRANS,
    0x0200: SCALE_TRANS,
    0x0400: SCALE_TRANS,
    0x0800: SCALE_TRANS,
}

def warning(messages: list[str] = [""], title: str = "Warning"):
    def draw(self, context):
        for message in messages:
            self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")


def insert_keyframe(obj, transform: int, frame: int, value: int) -> None:
    match transform:
        case 0x0008: #  "X Rot"
            obj.rotation_euler[0] = value * TransformValues[transform]
            obj.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)
        case 0x0010: #  "Y Rot"
            obj.rotation_euler[1] = value * TransformValues[transform]
            obj.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)
        case 0x0020: #  "Z Rot"
            obj.rotation_euler[2] = value * TransformValues[transform]
            obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)
        case 0x0040: #  "X Trans"
            obj.location[0] = value * TransformValues[transform] - obj.bone.head[0]
            obj.keyframe_insert(data_path="location", index=0, frame=frame)
        case 0x0080: #  "Y Trans"
            obj.location[1] = value * TransformValues[transform] - obj.bone.head[1]
            obj.keyframe_insert(data_path="location", index=1, frame=frame)
        case 0x0100: #  "Z Trans"
            obj.location[2] = value * TransformValues[transform] - obj.bone.head[2]
            obj.keyframe_insert(data_path="location", index=2, frame=frame)
        case 0x0200: #  "X Scale"
            obj.scale[0] = value * TransformValues[transform]
            obj.keyframe_insert(data_path="scale", index=0, frame=frame)
        case 0x0400: #  "Y Scale"
            obj.scale[1] = value * TransformValues[transform]
            obj.keyframe_insert(data_path="scale", index=1, frame=frame)
        case 0x0800: #  "Z Scale"
            obj.scale[2] = value * TransformValues[transform]
            obj.keyframe_insert(data_path="scale", index=2, frame=frame)


def do_bone_anim(file, bone, parent, warnings) -> None:
    transform_count, anim_size = unpack("2h", file.read(4))
    for _ in range(transform_count):
        transform_type, keyframe_count, transform_size = unpack("2HI", file.read(0x8))
        print(f'Transform at {hex(file.tell()-8)}: Type {transform_type} keyframe count {keyframe_count}')
        keyframes = [unpack("4h", file.read(0x8)) for _ in range(keyframe_count)]
        
        if transform_type not in TransformValues:
            warnings.append(f"Unsupported transform type: {hex(transform_type)}")
            continue

        [insert_keyframe(bone, transform_type, frame_idx, value) for value, frame_idx, _, _ in keyframes]
        
        kps = parent.animation_data.action.fcurves[-1].keyframe_points
        match transform_type:
                case 0x40:
                    offset = -bone.bone.head[0]
                case 0x80:
                    offset = -bone.bone.head[1]
                case 0x100:
                    offset = -bone.bone.head[2]
                case _:
                    offset = 0
        for kf in range(keyframe_count):
            kps[kf].interpolation = 'BEZIER'
            kps[kf].handle_left_type = 'FREE'
            kps[kf].handle_right_type = 'FREE'
            if kf == 0:
                prev_dt: float = 1
                next_dt: float = (keyframes[kf+1][1] - keyframes[kf][1]) / 3.0
                kps[kf].handle_left=(keyframes[kf][1] - prev_dt, (keyframes[kf][0]) * TransformValues[transform_type] + offset)
                kps[kf].handle_right=(keyframes[kf][1] + next_dt, (keyframes[kf][0] + keyframes[kf][3] * next_dt) * TransformValues[transform_type] + offset)
            elif kf == len(keyframes) - 1:
                prev_dt: float = (keyframes[kf][1] - keyframes[kf - 1][1]) / 3.0
                next_dt: float = 1
                kps[kf].handle_left=(keyframes[kf][1] - prev_dt, (keyframes[kf][0] - keyframes[kf][2] * prev_dt) * TransformValues[transform_type] + offset)
                kps[kf].handle_right=(keyframes[kf][1] + next_dt, (keyframes[kf][0]) * TransformValues[transform_type] + offset)
            else:
                prev_dt: float = (keyframes[kf][1] - keyframes[kf - 1][1]) / 3.0
                next_dt: float = (keyframes[kf+1][1] - keyframes[kf][1]) / 3.0
                kps[kf].handle_left=(keyframes[kf][1] - prev_dt, (keyframes[kf][0] - keyframes[kf][2] * prev_dt) * TransformValues[transform_type] + offset)
                kps[kf].handle_right=(keyframes[kf][1] + next_dt, (keyframes[kf][0] + keyframes[kf][3] * next_dt) * TransformValues[transform_type] + offset)
                

def import_anim(file, armature, missing_bones = None, bone_offset: int = 2) -> list[str]:
    if missing_bones is None:
        missing_bones =  []
    skipped_bones = 0
    warnings = []

    bone_count: int = unpack("i", file.read(4))[0]

    # Add bone keyframes
    file.seek(0xC, 1)
    for bone in range(bone_count):
        while bone + skipped_bones in missing_bones:
            skipped_bones += 1
        armature.pose.bones[bone + bone_offset + skipped_bones].rotation_mode = 'XYZ'
        print(f'Bone@{hex(file.tell())}')
        do_bone_anim(file, armature.pose.bones[bone + bone_offset + skipped_bones], parent=armature, warnings=warnings)
    
    bpy.data.scenes["Scene"].frame_start = 0
    bpy.data.scenes["Scene"].frame_end = int(max(curve.keyframe_points[-1].co[0] for curve in armature.animation_data.action.fcurves))

    return warnings


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
            if obj.animation_data is not None:
                obj.animation_data.action = bpy.data.actions.new(f'P3rd_Anim')
            warn = import_anim(
                file, 
                obj, 
                bone_offset=offset, 
                missing_bones=missing_bones
            )
            if warn:
                warning(list(set(warn)))
    except:
        warning(["Import Error"])
        return {'CANCELLED'}
    return {'FINISHED'}
