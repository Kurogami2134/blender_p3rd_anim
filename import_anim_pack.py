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
            file.seek(4)
            header_size = unpack("i", file.read(4))[0]
            file.seek(0)
            Header = unpack(f"{header_size//4}i", file.read(header_size))
            count = (Header[-1] - header_size - 4) // 4
            warnings = set()
            for offset_idx in range(count):
                file.seek(header_size + 4 + offset_idx * 4)
                offset = unpack("i", file.read(4))[0]
                if offset != -1:
                    print(f'Importing Anim_{offset_idx:0>3}.')
                    file.seek(offset)
                    obj.animation_data.action = bpy.data.actions.new(f'Anim_{offset_idx:0>3}')
                    warnings.update(import_anim(
                        file, 
                        obj, 
                        bone_offset=bone_offset, 
                        missing_bones=missing_bones
                    ))
            if warnings:
                warning(list(warnings))
    except:
        raise
        warning(["Import Error"])
        return {'CANCELLED'}
    return {'FINISHED'}
