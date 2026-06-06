from . import p3a_import_menu
from . import p3a_export_menu
from . import anim_pack_import_menu


bl_info = {
    "name": "P3rd Anim Import/Export",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}


def register():
    p3a_export_menu.register()
    p3a_import_menu.register()
    anim_pack_import_menu.register()


def unregister():
    p3a_export_menu.unregister()
    p3a_import_menu.unregister()
    anim_pack_import_menu.unregister()

if __name__ == "__main__":
    register()
