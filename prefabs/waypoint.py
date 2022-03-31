import bpy
from bpy.types import Operator
from ..gizmos.gizmo_group import update_gizmos


class HBAPrefabWaypointAdd(Operator):
    bl_idname = "object.hba_prefab_waypoint_add"
    bl_label = "Waypoint"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return {"FINISHED"}


operators = [HBAPrefabWaypointAdd]


def register():
    bpy.utils.register_class(HBAPrefabWaypointAdd)


def unregister():
    bpy.utils.unregister_class(HBAPrefabWaypointAdd)


if __name__ == "__main__":
    register()
