import bpy
from ..gizmos.gizmo_group import update_gizmos


class OBJECT_OT_hba_prefab_media_frame_add(bpy.types.Operator):
    bl_idname = "object.hba_prefab_media_frame_add"
    bl_label = "Add Media Frame"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.HBA_component_type = 'MEDIA_FRAME'
        update_gizmos(None, context)
        return {"FINISHED"}


class RENDER_PT_hba_prefab_media_frame(bpy.types.Panel):
    bl_idname = "HBA_PT_Prefab_Media_Frame"
    bl_label = "Media Frame"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return hasattr(context.active_object, "HBA_component_type") and context.active_object.HBA_component_type == 'MEDIA_FRAME'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj, "HBA_prefab_media_frame_prop_1")


def register():
    bpy.types.Object.HBA_prefab_media_frame_prop_1 = bpy.props.BoolProperty(
        name="Prop 1",
        description="Prop 1",
        default=False
    )
    bpy.utils.register_class(OBJECT_OT_hba_prefab_media_frame_add)
    bpy.utils.register_class(RENDER_PT_hba_prefab_media_frame)


def unregister():
    del bpy.types.Object.HBA_prefab_media_frame_prop_1
    bpy.utils.unregister_class(RENDER_PT_hba_prefab_media_frame)
    bpy.utils.unregister_class(OBJECT_OT_hba_prefab_media_frame_add)


if __name__ == "__main__":
    register()
