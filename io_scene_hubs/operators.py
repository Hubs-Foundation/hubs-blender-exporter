import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, CollectionProperty, PointerProperty
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

class CopyHubsComponent(Operator):
    bl_idname = "wm.copy_hubs_component"
    bl_label = "Copy component from active object"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        src_obj = context.active_object
        dest_objs = filter(lambda item: src_obj != item, context.selected_objects)

        hubs_settings = context.scene.hubs_settings
        component_class = hubs_settings.registered_hubs_components[self.component_name]
        component_class_name = component_class.__name__
        component_definition = hubs_settings.hubs_config['components'][self.component_name]

        if components.has_component(src_obj, self.component_name):
            for dest_obj in dest_objs:
                if components.has_component(dest_obj, self.component_name):
                    components.remove_component(dest_obj, self.component_name)

                components.add_component(
                    dest_obj,
                    self.component_name,
                    hubs_settings.hubs_config,
                    hubs_settings.registered_hubs_components
                )

                src_component = getattr(src_obj, component_class_name)
                dest_component = getattr(dest_obj, component_class_name)

                self.copy_type(hubs_settings, src_component, dest_component, component_definition)

        return{'FINISHED'}


    def copy_type(self, hubs_settings, src_obj, dest_obj, type_definition):
        for property_name, property_definition in type_definition['properties'].items():
            self.copy_property(hubs_settings, src_obj, dest_obj, property_name, property_definition)

    def copy_property(self, hubs_settings, src_obj, dest_obj, property_name, property_definition):
        property_type = property_definition['type']

        if property_type == 'collections':
            return

        registered_types = hubs_settings.hubs_config['types']
        is_custom_type = property_type in registered_types

        src_property = getattr(src_obj, property_name)
        dest_property = getattr(dest_obj, property_name)

        if is_custom_type:
            dest_obj[property_name] = self.copy_type(hubs_settings, src_property, dest_property, registered_types[property_type])
        elif property_type == 'array':
            self.copy_array_property(hubs_settings, src_property, dest_property, property_definition)
        else:
            setattr(dest_obj, property_name, src_property)

    def copy_array_property(self, hubs_settings, src_arr, dest_arr, property_definition):
        array_type = property_definition['arrayType']
        registered_types = hubs_settings.hubs_config['types']
        type_definition = registered_types[array_type]

        dest_arr.clear()

        for src_item in src_arr:
            dest_item = dest_arr.add()
            self.copy_type(hubs_settings, src_item, dest_item, type_definition)


class RemoveHubsComponentItem(Operator):
    bl_idname = "wm.remove_hubs_component_item"
    bl_label = "Remove an item"

    path: StringProperty(name="path")

    def execute(self, context):
        parts = self.path.split(".")

        index = int(parts.pop())

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
    bpy.utils.register_class(CopyHubsComponent)
    bpy.utils.register_class(AddHubsComponentItem)
    bpy.utils.register_class(RemoveHubsComponentItem)
    bpy.utils.register_class(ReloadHubsConfig)
    bpy.utils.register_class(ExportHubsGLTF)

def unregister():
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
    bpy.utils.unregister_class(CopyHubsComponent)
    bpy.utils.unregister_class(AddHubsComponentItem)
    bpy.utils.unregister_class(RemoveHubsComponentItem)
    bpy.utils.unregister_class(ReloadHubsConfig)
    bpy.utils.unregister_class(ExportHubsGLTF)
