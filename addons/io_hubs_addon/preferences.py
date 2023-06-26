import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty
from .utils import get_addon_package
import platform
from os.path import join, dirname, realpath


def get_addon_pref(context):
    addon_package = get_addon_package()
    return context.preferences.addons[addon_package].preferences


def get_recast_lib_path():
    recast_lib = join(dirname(realpath(__file__)), "bin", "recast")

    file_name = None
    if platform.system() == 'Windows':
        file_name = "RecastBlenderAddon.dll"
    elif platform.system() == 'Darwin':
        file_name = "libRecastBlenderAddon.dylib"
    else:
        file_name = "libRecastBlenderAddon.so"

    return join(recast_lib, file_name)


class HubsPreferences(AddonPreferences):
    bl_idname = __package__

    row_length: IntProperty(
        name="Add Component Menu Row Length",
        description="Allows you to control how many categories are added to a row before it starts on the next row. Set to 0 to have it all on one row",
        default=4,
        min=0,
    )

    recast_lib_path: StringProperty(
        name='Recast library path',
        subtype='FILE_PATH',
        default=get_recast_lib_path()
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")
        box.row().prop(self, "recast_lib_path")


def register():
    bpy.utils.register_class(HubsPreferences)


def unregister():
    bpy.utils.unregister_class(HubsPreferences)
