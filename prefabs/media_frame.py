import bpy
from bpy.types import Object, Operator, Panel
from ..gizmos.gizmo_group import update_gizmos


class HBAPrefabMediaFrameAdd(Operator):
    bl_idname = "object.hba_prefab_media_frame_add"
    bl_label = "Media Frame"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        obj = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.hubs_gizmo_type = 'MEDIA_FRAME'
        update_gizmos(None, context)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return {"FINISHED"}


class HBAPrefabMediaFramePanel(Panel):
    bl_idname = "HBA_PT_Prefab_Media_Frame"
    bl_label = "Media Frame"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return hasattr(context.active_object, "hubs_gizmo_type") and context.active_object.hubs_gizmo_type == 'MEDIA_FRAME'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj, "HBA_prefab_media_frame_prop_1")

operators = [HBAPrefabMediaFrameAdd]

def register():
    Object.HBA_prefab_media_frame_prop_1 = bpy.props.BoolProperty(
        name="Prop 1",
        description="Prop 1",
        default=False
    )
    bpy.utils.register_class(HBAPrefabMediaFrameAdd)
    bpy.utils.register_class(HBAPrefabMediaFramePanel)


def unregister():
    del Object.HBA_prefab_media_frame_prop_1
    bpy.utils.unregister_class(HBAPrefabMediaFramePanel)
    bpy.utils.unregister_class(HBAPrefabMediaFrameAdd)


if __name__ == "__main__":
    register()
