import bpy
from ..gizmos.gizmo_group import update_gizmos


class OBJECT_OT_hba_prefab_waypoint_add(bpy.types.Operator):
    bl_idname = "object.hba_prefab_waypoint_add"
    bl_label = "Add Waypoint"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.HBA_component_type = 'WAYPOINT'
        update_gizmos(None, context)
        return {"FINISHED"}


class RENDER_PT_hba_prefab_waypoint(bpy.types.Panel):
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


def register():
    bpy.types.Object.HBA_waypoint_prop_can_be_spawn_point = bpy.props.BoolProperty(
        name="Can be spawn point",
        description="Can this waypoint be a spawn point",
        default=False
    )
    bpy.types.Object.HBA_waypoint_prop_can_be_occupied = bpy.props.BoolProperty(
        name="Can be occupied",
        description="Can this waypoint be occupied",
        default=False
    )
    bpy.types.Object.HBA_waypoint_prop_can_be_clicked = bpy.props.BoolProperty(
        name="Can be clicked",
        description="Can this waypoint be clicked",
        default=False
    )
    bpy.types.Object.HBA_waypoint_prop_will_disable_motion = bpy.props.BoolProperty(
        name="Will disable motion",
        description="This waypoint will disable avatars motion",
        default=False
    )
    bpy.types.Object.HBA_waypoint_prop_will_disable_teleporting = bpy.props.BoolProperty(
        name="Will disable teleporting",
        description="This waypoint will disable avatar's teleporting",
        default=False
    )
    bpy.types.Object.HBA_waypoint_prop_snap_to_nav_mesh = bpy.props.BoolProperty(
        name="Snap to nav mesh",
        description="Snap to nav mesh",
        default=False
    )
    bpy.utils.register_class(OBJECT_OT_hba_prefab_waypoint_add)
    bpy.utils.register_class(RENDER_PT_hba_prefab_waypoint)


def unregister():
    del bpy.types.Object.HBA_waypoint_prop_can_be_spawn_point
    del bpy.types.Object.HBA_waypoint_prop_can_be_occupied
    del bpy.types.Object.HBA_waypoint_prop_can_be_clicked
    del bpy.types.Object.HBA_waypoint_prop_will_disable_motion
    del bpy.types.Object.HBA_waypoint_prop_will_disable_teleporting
    del bpy.types.Object.HBA_waypoint_prop_snap_to_nav_mesh
    bpy.utils.unregister_class(RENDER_PT_hba_prefab_waypoint)
    bpy.utils.unregister_class(OBJECT_OT_hba_prefab_waypoint_add)


if __name__ == "__main__":
    register()
