import bpy
from bpy.types import Object, Operator, Panel
from ..gizmos.gizmo_group import update_gizmos


class HBAPrefabAudioZoneAdd(Operator):
    bl_idname = "object.hba_prefab_audio_zone_add"
    bl_label = "Audio Zone"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.hubs_gizmo_type = 'AUDIO_ZONE'
        update_gizmos(None, context)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return {"FINISHED"}


class HBAPrefabAudioZonePanel(Panel):
    bl_idname = "HBA_PT_Prefab_Audio_Zone"
    bl_label = "Audio Zone"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return hasattr(context.active_object, "hubs_gizmo_type") and context.active_object.hubs_gizmo_type == 'AUDIO_ZONE'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj, "HBA_prefab_audio_zone_prop_1")

operators = [HBAPrefabAudioZoneAdd]

def register():
    Object.HBA_prefab_audio_zone_prop_1 = bpy.props.BoolProperty(
        name="Prop 1",
        description="Prop 1",
        default=False
    )
    bpy.utils.register_class(HBAPrefabAudioZoneAdd)
    bpy.utils.register_class(HBAPrefabAudioZonePanel)


def unregister():
    del Object.HBA_prefab_audio_zone_prop_1
    bpy.utils.unregister_class(HBAPrefabAudioZonePanel)
    bpy.utils.unregister_class(HBAPrefabAudioZoneAdd)


if __name__ == "__main__":
    register()
