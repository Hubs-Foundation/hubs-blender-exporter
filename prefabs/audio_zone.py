import bpy
from bpy.types import Object, Operator
from ..gizmos.gizmo_group import update_gizmos
from ..components.utils import *

class HBAPrefabAudioZoneAdd(Operator):
    bl_idname = "object.hba_prefab_audio_zone_add"
    bl_label = "Audio Zone"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return {"FINISHED"}

operators = [HBAPrefabAudioZoneAdd]

def register():
    bpy.utils.register_class(HBAPrefabAudioZoneAdd)


def unregister():
    del Object.HBA_prefab_audio_zone_prop_1
    bpy.utils.unregister_class(HBAPrefabAudioZoneAdd)


if __name__ == "__main__":
    register()
