import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty
from enum import Enum

from .utils import get_addon_package


class HubsPreference(Enum):
    ROW_LENGTH = 'row_length'
    TMP_PATH = 'tmp_path'


def get_addon_pref(pref):
    addon_package = get_addon_package()
    addon_prefs = bpy.context.preferences.addons[addon_package].preferences
    return getattr(addon_prefs, pref.value)


class HubsPreferences(AddonPreferences):
    bl_idname = __package__

    row_length: IntProperty(
        name="Add Component Menu Row Length",
        description="Allows you to control how many categories are added to a row before it starts on the next row. Set to 0 to have it all on one row",
        default=4,
        min=0,
    )

    tmp_path: StringProperty(
        name="Temporary files path",
        description="Path where temporary files will be stored.",
        subtype="DIR_PATH",
        default="//generated_cubemaps/"
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")
        box.row().prop(self, "tmp_path")


def register():
    bpy.utils.register_class(HubsPreferences)


def unregister():
    bpy.utils.unregister_class(HubsPreferences)
