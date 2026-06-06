import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty

from . import import_p3a


class ImportP3A(Operator, ImportHelper):
    """Import MHP3rd anim entries (p3a)."""
    bl_idname = "import_mh.p3a"
    bl_label = "Import P3A"

    filename_ext = ".p3a"

    offset: IntProperty(
        name="Bone Offset",
        description="Offset from bone 0.",
        default=2,
    )
    
    filter_glob: StringProperty(
        default="*.p3a",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    missing_bones: StringProperty(
        name="Bones to skip",
        default="",
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return import_p3a.execute(
            context,
            filepath=self.filepath,
            offset=self.offset,
            missing=self.missing_bones,
        )


def menu_func_import(self, context):
    self.layout.operator(ImportP3A.bl_idname, text="MHP3rd P3A")


def register():
    bpy.utils.register_class(ImportP3A)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportP3A)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
