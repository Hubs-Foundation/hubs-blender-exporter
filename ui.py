import bpy


class OBJECT_OT_hba_settings_export(bpy.types.Operator):
    bl_idname = "object.hba_settings_export"
    bl_label = "Render"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return {"FINISHED"}


class OBJECT_PT_hba_settings_panel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hubs'


class OBJECT_PT_hba_settings_prefabs(OBJECT_PT_hba_settings_panel, bpy.types.Panel):
    bl_idname = "OBJECT_PT_hba_settings_prefabs"
    bl_label = "Prefabs"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.hba_waypoint_add", text="Add Waypoint")
        row = layout.row()
        row.operator("object.hba_media_frame_add", text="Add Media Frame")
        row = layout.row()
        row.operator("object.hba_audio_zone_add", text="Add Audio Zone")

        row = layout.row()


class OBJECT_PT_hba_settings_components(OBJECT_PT_hba_settings_panel, bpy.types.Panel):
    bl_idname = "OBJECT_PT_hba_settings_components"
    bl_label = "Components"

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.hba_component_visible_add",
                     text="Visible")
        row = layout.row()

        row = layout.row()


class OBJECT_PT_hba_settings_export(OBJECT_PT_hba_settings_panel, bpy.types.Panel):
    bl_idname = "OBJECT_PT_hba_settings_export"
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.hba_settings_export", text="Export")

        row = layout.row()
        row.prop(context.scene.hba_settings,
                 "output_path", text="Output Path")

        row = layout.row()


classes = (
    OBJECT_OT_hba_settings_export,
    OBJECT_PT_hba_settings_prefabs,
    OBJECT_PT_hba_settings_components,
    OBJECT_PT_hba_settings_export
)

register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()
