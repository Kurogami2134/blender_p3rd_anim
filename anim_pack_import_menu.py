import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty

from . import import_anim_pack


class ImportAnimPack(Operator, ImportHelper):
    """Import MHP3rd anim pack."""
    bl_idname = "import_mh.anim_pack"
    bl_label = "Import P3rd Animation Pack"

    filename_ext = ".bin"

    offset: IntProperty(
        name="Bone Offset",
        description="Offset from bone 0.",
        default=2,
    )
    
    filter_glob: StringProperty(
        default="*.*",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    missing_bones: StringProperty(
        name="Bones to skip",
        default="",
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return import_anim_pack.execute(
            context,
            filepath=self.filepath,
            bone_offset=self.offset,
            missing=self.missing_bones,
        )


def menu_func_import(self, context):
    self.layout.operator(ImportAnimPack.bl_idname, text="MHP3rd Anim Pack")


def register():
    bpy.utils.register_class(ImportAnimPack)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportAnimPack)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
