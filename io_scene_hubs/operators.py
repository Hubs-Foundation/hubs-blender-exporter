import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from . import components
from . import exporter

class AddHubsSceneComponent(Operator):
    bl_idname = "wm.add_hubs_scene_component"
    bl_label = "Add Hubs Component to Scene"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        components.add_component(
            context.scene,
            self.component_name,
            context.scene.hubs_settings.hubs_config,
            context.scene.hubs_settings.registered_hubs_components
        )

        context.area.tag_redraw()
        return {'FINISHED'}

class AddHubsObjectComponent(Operator):
    bl_idname = "wm.add_hubs_object_component"
    bl_label = "Add Hubs Component to Object"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        components.add_component(
            context.object,
            self.component_name,
            context.scene.hubs_settings.hubs_config,
            context.scene.hubs_settings.registered_hubs_components
        )

        context.area.tag_redraw()
        return {'FINISHED'}

class RemoveHubsSceneComponent(Operator):
    bl_idname = "wm.remove_hubs_scene_component"
    bl_label = "Remove Hubs Component from Scene"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        components.remove_component(context.scene, self.component_name)
        context.area.tag_redraw()
        return {'FINISHED'}

class RemoveHubsObjectComponent(Operator):
    bl_idname = "wm.remove_hubs_object_component"
    bl_label = "Remove Hubs Component from Object"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        components.remove_component(context.object, self.component_name)
        context.area.tag_redraw()
        return {'FINISHED'}

class ReloadHubsConfig(Operator):
    bl_idname = "wm.reload_hubs_config"
    bl_label = "Reload Hubs Config"

    def execute(self, context):
        context.scene.hubs_settings.reload_config()
        context.area.tag_redraw()
        return {'FINISHED'}

class ExportHubsGLTF(Operator):
    bl_idname = "wm.export_hubs_gltf"
    bl_label = "Export Hubs GLTF"

    selected: BoolProperty(name="selected", default=False)

    def execute(self, context):
        try:
            filepath = exporter.export(
                context.scene,
                self.selected,
                context.scene.hubs_settings.hubs_config,
                context.scene.hubs_settings.registered_hubs_components
            )
            self.report({'INFO'}, 'Project saved to \"%s\"' % (filepath))
            return {'FINISHED'}
        except RuntimeError as error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(AddHubsSceneComponent)
    bpy.utils.register_class(RemoveHubsSceneComponent)
    bpy.utils.register_class(AddHubsObjectComponent)
    bpy.utils.register_class(RemoveHubsObjectComponent)
    bpy.utils.register_class(ReloadHubsConfig)
    bpy.utils.register_class(ExportHubsGLTF)

def unregister():
    bpy.utils.unregister_class(AddHubsSceneComponent)
    bpy.utils.unregister_class(RemoveHubsSceneComponent)
    bpy.utils.unregister_class(AddHubsObjectComponent)
    bpy.utils.unregister_class(RemoveHubsObjectComponent)
    bpy.utils.unregister_class(ReloadHubsConfig)
    bpy.utils.unregister_class(ExportHubsGLTF)
