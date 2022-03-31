import bpy
from bpy.types import Object, Operator
from ..gizmos.gizmo_group import update_gizmos
from ..components.utils import *

class HBAPrefabMediaFrameAdd(Operator):
    bl_idname = "object.hba_prefab_media_frame_add"
    bl_label = "Media Frame"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        update_gizmos(None, context)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return {"FINISHED"}

operators = [HBAPrefabMediaFrameAdd]

def register():
    bpy.utils.register_class(HBAPrefabMediaFrameAdd)


def unregister():
    del Object.HBA_prefab_media_frame_prop_1
    bpy.utils.unregister_class(HBAPrefabMediaFrameAdd)


if __name__ == "__main__":
    register()
