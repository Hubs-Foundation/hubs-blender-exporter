import bpy
from bpy.types import Object, Operator, Panel, Menu
from ..gizmos.gizmo_group import update_gizmos

class HBAPrefabWaypointAdd(Operator):
    bl_idname = "object.hba_prefab_waypoint_add"
    bl_label = "Waypoint"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.HBA_component_type = 'WAYPOINT'
        update_gizmos(None, context)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return {"FINISHED"}

class LilyGizmosAddMenu(Menu):
    bl_label = "Hubs"
    bl_idname = "VIEW3D_MT_hubs_add_menu"

    def draw(self, context):
        self.layout.operator(HBAPrefabWaypointAdd.bl_idname, icon='MESH_CUBE')

class HBAPrefabWaypointPanel(Panel):
    bl_idname = "HBA_PT_Prefab_Waypoint"
    bl_label = "Waypoint"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return hasattr(context.active_object, "HBA_component_type") and context.active_object.HBA_component_type == 'WAYPOINT'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj, "HBA_waypoint_prop_can_be_spawn_point")
        row = layout.row()
        row.prop(obj, "HBA_waypoint_prop_can_be_occupied")
        row = layout.row()
        row.prop(obj, "HBA_waypoint_prop_can_be_clicked")
        row = layout.row()
        row.prop(obj, "HBA_waypoint_prop_will_disable_motion")
        row = layout.row()
        row.prop(obj, "HBA_waypoint_prop_will_disable_teleporting")
        row = layout.row()
        row.prop(obj, "HBA_waypoint_prop_snap_to_nav_mesh")

operators = [HBAPrefabWaypointAdd]

def register():
    Object.HBA_waypoint_prop_can_be_spawn_point = bpy.props.BoolProperty(
        name="Can be spawn point",
        description="Can this waypoint be a spawn point",
        default=False
    )
    Object.HBA_waypoint_prop_can_be_occupied = bpy.props.BoolProperty(
        name="Can be occupied",
        description="Can this waypoint be occupied",
        default=False
    )
    Object.HBA_waypoint_prop_can_be_clicked = bpy.props.BoolProperty(
        name="Can be clicked",
        description="Can this waypoint be clicked",
        default=False
    )
    Object.HBA_waypoint_prop_will_disable_motion = bpy.props.BoolProperty(
        name="Will disable motion",
        description="This waypoint will disable avatars motion",
        default=False
    )
    Object.HBA_waypoint_prop_will_disable_teleporting = bpy.props.BoolProperty(
        name="Will disable teleporting",
        description="This waypoint will disable avatar's teleporting",
        default=False
    )
    Object.HBA_waypoint_prop_snap_to_nav_mesh = bpy.props.BoolProperty(
        name="Snap to nav mesh",
        description="Snap to nav mesh",
        default=False
    )
    bpy.utils.register_class(HBAPrefabWaypointAdd)
    bpy.utils.register_class(HBAPrefabWaypointPanel)

def unregister():
    del Object.HBA_waypoint_prop_can_be_spawn_point
    del Object.HBA_waypoint_prop_can_be_occupied
    del Object.HBA_waypoint_prop_can_be_clicked
    del Object.HBA_waypoint_prop_will_disable_motion
    del Object.HBA_waypoint_prop_will_disable_teleporting
    del Object.HBA_waypoint_prop_snap_to_nav_mesh
    bpy.utils.unregister_class(HBAPrefabWaypointPanel)
    bpy.utils.unregister_class(HBAPrefabWaypointAdd)


if __name__ == "__main__":
    register()
