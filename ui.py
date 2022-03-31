import bpy


class HBASettingsExport(bpy.types.Operator):
    bl_idname = "object.hba_settings_export"
    bl_label = "Render"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return {"FINISHED"}


class HBASettingsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hubs'


class HBASettingsPrefabsPanel(HBASettingsPanel, bpy.types.Panel):
    bl_idname = "HBA_PT_Settings_Prefabs"
    bl_label = "Prefabs"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.hba_prefab_waypoint_add", text="Add Waypoint")
        row = layout.row()
        row.operator("object.hba_prefab_media_frame_add",
                     text="Add Media Frame")
        row = layout.row()
        row.operator("object.hba_prefab_audio_zone_add", text="Add Audio Zone")

        row = layout.row()


class HBASettingsComponentsPanel(HBASettingsPanel, bpy.types.Panel):
    bl_idname = "HBA_PT_Settings_Components"
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
        row.operator("object.hba_component_waypoint_add",
                     text="Waypoint")
        row = layout.row()


class HBASettingsExportPanel(HBASettingsPanel, bpy.types.Panel):
    bl_idname = "HBA_PT_Settings_Export"
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
    HBASettingsExport,
    HBASettingsPrefabsPanel,
    HBASettingsComponentsPanel,
    HBASettingsExportPanel
)

register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()
