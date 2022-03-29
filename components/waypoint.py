import bpy
from bpy.props import BoolProperty, PointerProperty
from bpy.types import PropertyGroup

class WaypointComponentProperties(PropertyGroup):
    waypoint: BoolProperty(name="Waypoint", default=True)

class HBAComponentWaypointAdd(bpy.types.Operator):
    bl_idname = "object.hba_component_waypoint_add"
    bl_label = "Add Waypoint Component"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return {"FINISHED"}


class HBAComponentWaypointPanel(bpy.types.Panel):
    bl_idname = "HBA_PT_Component_Waypoint"
    bl_label = "Waypoint Component"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        # TODO Add check to see if the component Waypoint has been added
        return context.object.type == 'MESH'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj.HBA_object_component_waypoint,
                 "waypoint", text="waypoint")
        row = layout.row()


def register():
    bpy.utils.register_class(WaypointComponentProperties)
    bpy.types.Object.HBA_object_component_waypoint = PointerProperty(
        type=WaypointComponentProperties)
    bpy.utils.register_class(HBAComponentWaypointAdd)
    bpy.utils.register_class(HBAComponentWaypointPanel)


def unregister():
    bpy.utils.unregister_class(HBAComponentWaypointPanel)
    bpy.utils.unregister_class(HBAComponentWaypointAdd)
    del bpy.types.Object.HBA_object_component_waypoint
    bpy.utils.unregister_class(WaypointComponentProperties)
