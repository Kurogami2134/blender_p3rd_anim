import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator
from bpy.props import IntProperty, BoolProperty, StringProperty

from . import export_p3a


class ExportP3A(Operator, ExportHelper):
    """Export MHP3rd anim entries (p3a)."""
    bl_idname = "export_mh.p3a"
    bl_label = "Export P3A"

    filename_ext = ".p3a"

    offset: IntProperty(
        name="Bone Offset",
        description="Offset from bone 0.",
        default=2,
    )

    loop: BoolProperty(
        name="Loop",
        description="Set 1 for infinite loop.",
        default=True,
    )
    
    filter_glob: StringProperty(
        default="*.p3a",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    missing_bones: StringProperty(
        default="",
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return export_p3a.execute(
            context,
            filepath=self.filepath,
            offset=self.offset,
            loop=self.loop,
            missing=self.missing_bones,
        )


def menu_func_export(self, context):
    self.layout.operator(ExportP3A.bl_idname, text="MHP3rd P3A")


def register():
    bpy.utils.register_class(ExportP3A)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportP3A)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
