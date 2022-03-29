import bpy
from ..gizmos.gizmo_group import update_gizmos


class OBJECT_OT_hba_prefab_audio_zone_add(bpy.types.Operator):
    bl_idname = "object.hba_prefab_audio_zone_add"
    bl_label = "Add Audio Zone"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.HBA_component_type = 'AUDIO_ZONE'
        update_gizmos(None, context)
        return {"FINISHED"}


class RENDER_PT_hba_prefab_audio_zone(bpy.types.Panel):
    bl_idname = "HBA_PT_Prefab_Audio_Zone"
    bl_label = "Audio Zone"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return hasattr(context.active_object, "HBA_component_type") and context.active_object.HBA_component_type == 'AUDIO_ZONE'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj, "HBA_prefab_audio_zone_prop_1")


def register():
    bpy.types.Object.HBA_prefab_audio_zone_prop_1 = bpy.props.BoolProperty(
        name="Prop 1",
        description="Prop 1",
        default=False
    )
    bpy.utils.register_class(OBJECT_OT_hba_prefab_audio_zone_add)
    bpy.utils.register_class(RENDER_PT_hba_prefab_audio_zone)


def unregister():
    del bpy.types.Object.HBA_prefab_audio_zone_prop_1
    bpy.utils.unregister_class(RENDER_PT_hba_prefab_audio_zone)
    bpy.utils.unregister_class(OBJECT_OT_hba_prefab_audio_zone_add)


if __name__ == "__main__":
    register()
