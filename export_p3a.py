import bpy
from math import radians
from struct import pack


ROTATION_SCALE = radians(1 / 0x1000 * 90)


TransformRemap: dict[str, int] = {
    "location_x": 0x0040,
    "location_y": 0x0080,
    "location_z": 0x0100,
    "rotation_euler_x": 0x0008,
    "rotation_euler_y": 0x0010,
    "rotation_euler_z": 0x0020,
    "scale_x": 0x0200,
    "scale_y": 0x0400,
    "scale_z": 0x0800,
}


def warning(messages: list[str] = [""], title: str = "Warning"):
    def draw(self, context):
        for message in messages:
            self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")




def export_anim(file, armature, missing_bones = None, bone_offset: int = 2, loop: bool = True, bone_count: int | None = None):
    def get_bone_idx(info_path: str) -> int:
        return armature.pose.bones.find(info_path.split("[\"")[1].split("\"]")[0])
    
    def get_value(value: int, transform_type: str) -> int:
        match transform_type:
            case "location":
                return int(value * 0x10)
            case "scale":
                return int(value * 0x100)
            case "rotation_euler":
                return int(value / ROTATION_SCALE)
            case _:
                return 0

    if missing_bones is None:
        missing_bones =  []
    
    bones = {}
    for curve in armature.animation_data.action.fcurves:
        bone_idx = get_bone_idx(curve.data_path) - bone_offset
        if bone_idx not in bones:
            bones[bone_idx] = []
        bones[bone_idx].append({
            "transform": f'{curve.data_path.split(".")[-1]}_{["x", "y", "z"][curve.array_index]}',
            "keyframes": [(int(x.co[0]), get_value(x.co[1], curve.data_path.split(".")[-1])) for x in curve.keyframe_points],
        })

    file.seek(0x10)
    bone_count = (max(bones.keys()) + 1) if bone_count is None else bone_count
    for idx in range(bone_count):
        if idx in missing_bones:
            continue
        print(f'Bone{idx}')
        if idx in bones:
            add = file.tell()
            file.seek(4, 1)
            for transform in bones[idx]:
                file.write(pack("2hi", TransformRemap[transform["transform"]], len(transform["keyframes"]), len(transform["keyframes"]) * 8 + 8))
                for kf in transform["keyframes"]:
                    file.write(pack("2h4x", kf[1], kf[0]))
            add2 = file.tell()
            file.seek(add)
            file.write(pack("2h", len(bones[idx]), add2-add))
            file.seek(add2)
        else:
            file.write(pack('2h', 0, 4))

    size = file.tell()
    file.seek(0)
    file.write(pack("3i4x", (max(bones.keys()) + 1 - len(missing_bones)) if bone_count is None else bone_count, size, 1 if loop else 0))


def execute(c, filepath: str, offset: int, loop: bool, missing: str, bone_count: int) -> set[str]:
    obj = c.active_object
    if obj.type != 'ARMATURE':
        warning(["Active object is not an armature."])
        return {'CANCELLED'}
    if missing == '':
        missing_bones: list | None = None
    else:
        missing_bones: list | None = [int(x) for x in missing.split(",")]
    try:
        with open(filepath, "wb") as file:
            export_anim(
                file=file, 
                armature=obj, 
                bone_offset=offset, 
                loop=loop, 
                missing_bones=missing_bones, 
                bone_count=None if bone_count == -1 else bone_count
            )
    except:
        warning(["Export Error"])
        return {'CANCELLED'}
    return {'FINISHED'}
