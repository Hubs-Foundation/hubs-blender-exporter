import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator
from . import components
from . import exporter

class AddHubsComponent(Operator):
    bl_idname = "wm.add_hubs_component"
    bl_label = "Add Hubs Component"
    bl_property = "component_name"

    object_source: StringProperty(name="object_source")

    def get_items(self, context):
        hubs_components = bpy.context.scene.hubs_settings.registered_hubs_components

        items = []

        obj = components.get_object_source(context, self.object_source)

        for component_name, component_class in hubs_components.items():
            if (components.is_object_source_component(self.object_source, component_class.definition)
                and not components.has_component(obj, component_name)):
                items.append((component_name, component_name, ''))

        return items

    component_name: EnumProperty(name="component_name", items=get_items)

    def execute(self, context):
        if self.component_name == '':
            return

        obj = components.get_object_source(context, self.object_source)

        components.add_component(
            obj,
            self.component_name,
            context.scene.hubs_settings.hubs_config,
            context.scene.hubs_settings.registered_hubs_components
        )

        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

class RemoveHubsComponent(Operator):
    bl_idname = "wm.remove_hubs_component"
    bl_label = "Remove Hubs Component"

    object_source: StringProperty(name="object_source")
    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return
        obj = components.get_object_source(context, self.object_source)
        components.remove_component(obj, self.component_name)
        context.area.tag_redraw()
        return {'FINISHED'}

class AddHubsComponentItem(Operator):
    bl_idname = "wm.add_hubs_component_item"
    bl_label = "Add a new item"

    path: StringProperty(name="path")

    def execute(self, context):
        parts = self.path.split(".")

        cur_obj = context

        for part in parts:
            try:
                index = int(part)
                cur_obj = cur_obj[index]
            except:
                cur_obj = getattr(cur_obj, part)

        cur_obj.add()

        context.area.tag_redraw()

        return{'FINISHED'}

class RemoveHubsComponentItem(Operator):
    bl_idname = "wm.remove_hubs_component_item"
    bl_label = "Remove an item"

    path: StringProperty(name="path")

    def execute(self, context):
        parts = self.path.split(".")

        index = int(parts.pop())

        print(index, parts)

        cur_obj = context

        for part in parts:
            try:
                cur_index = int(part)
                cur_obj = cur_obj[cur_index]
            except:
                cur_obj = getattr(cur_obj, part)

        cur_obj.remove(index)

        context.area.tag_redraw()

        return{'FINISHED'}

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
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)
    bpy.utils.register_class(AddHubsComponentItem)
    bpy.utils.register_class(RemoveHubsComponentItem)
    bpy.utils.register_class(ReloadHubsConfig)
    bpy.utils.register_class(ExportHubsGLTF)

def unregister():
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
    bpy.utils.unregister_class(AddHubsComponentItem)
    bpy.utils.unregister_class(RemoveHubsComponentItem)
    bpy.utils.unregister_class(ReloadHubsConfig)
    bpy.utils.unregister_class(ExportHubsGLTF)
