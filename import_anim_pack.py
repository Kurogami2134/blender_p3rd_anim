import bpy
from struct import unpack
from .import_p3a import import_anim, warning

def execute(c, filepath: str, bone_offset: int, missing: str) -> set[str]:
    obj = c.active_object
    if obj.type != 'ARMATURE':
        warning(["Active object is not an armature."])
        return {'CANCELLED'}
    if missing == '':
        missing_bones: list | None = None
    else:
        missing_bones: list | None = [int(x) for x in missing.split(",")]

    try:
        if obj.animation_data is None:
            obj.animation_data_create()
        with open(filepath, "rb") as file:
            Header = unpack("8i", file.read(0x20))
            count = int(Header[-1] / 4) - 9
            for offset_idx in range(count):
                file.seek(0x24 + offset_idx * 4)
                offset = unpack("i", file.read(4))[0]
                if offset != -1:
                    print(f'Importing Anim_{offset_idx:0>3}.')
                    file.seek(offset)
                    obj.animation_data.action = bpy.data.actions.new(f'Anim_{offset_idx:0>3}')
                    import_anim(file, obj, bone_offset=bone_offset, missing_bones=missing_bones)
    except:
        raise
        warning(["Import Error"])
        return {'CANCELLED'}
    return {'FINISHED'}
