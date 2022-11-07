import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty
from enum import Enum

from .utils import get_addon_package


def get_addon_pref(context):
    addon_package = get_addon_package()
    return context.preferences.addons[addon_package].preferences


class HubsPreferences(AddonPreferences):
    bl_idname = __package__

    row_length: IntProperty(
        name="Add Component Menu Row Length",
        description="Allows you to control how many categories are added to a row before it starts on the next row. Set to 0 to have it all on one row",
        default=4,
        min=0,
    )

    ref_probe_path: StringProperty(
        name="Reflection Probe Output Directory",
        description="Path where Reflection Probe bakes will be stored",
        subtype="DIR_PATH",
        default="//generated_cubemaps/"
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")
        box.row().prop(self, "ref_probe_path")
        if not bpy.data.filepath:
            ref_probe_path_notice = box.column()
            ref_probe_path_notice.scale_y = 0.7
            ref_probe_path_notice.alert = True
            ref_probe_path_notice.label(
                text=f"New file detected, redirecting output directory to: {bpy.app.tempdir}", icon='ERROR')
            ref_probe_path_notice.label(
                text=f"The contents will be transferred to the main directory when the blend file is saved", icon='BLANK1')


def register():
    bpy.utils.register_class(HubsPreferences)


def unregister():
    bpy.utils.unregister_class(HubsPreferences)
