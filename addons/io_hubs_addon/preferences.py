import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty

class HubsPreferences(AddonPreferences):
    bl_idname = __package__

    row_length: IntProperty(
        name="Add Component Menu Row Length",
        description="Allows you to control how many categories are added to a row before it starts on the next row. Set to 0 to have it all on one row",
        default=4,
        min=0,
        )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")


def register():
    bpy.utils.register_class(HubsPreferences)

def unregister():
    bpy.utils.unregister_class(HubsPreferences)
