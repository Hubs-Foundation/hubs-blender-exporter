import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy.types import Operator
from . import components

class AddMozComponent(Operator):
    bl_idname = "wm.add_mozcomponents_component"
    bl_label = "Add MOZ Component"
    bl_property = "component_name"

    object_source: StringProperty(name="object_source")

    def get_items(self, context):
        moz_components = bpy.context.scene.mozcomponents_settings.registered_moz_components

        items = []

        obj = components.get_object_source(context, self.object_source)

        for component_name, component_class in moz_components.items():
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
            context.scene.mozcomponents_settings.mozcomponents_config,
            context.scene.mozcomponents_settings.registered_moz_components
        )

        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

class RemoveMozComponent(Operator):
    bl_idname = "wm.remove_mozcomponents_component"
    bl_label = "Remove Moz Component"

    object_source: StringProperty(name="object_source")
    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return
        obj = components.get_object_source(context, self.object_source)
        components.remove_component(obj, self.component_name)
        context.area.tag_redraw()
        return {'FINISHED'}

class AddMozComponentItem(Operator):
    bl_idname = "wm.add_mozcomponents_component_item"
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

class CopyMozComponent(Operator):
    bl_idname = "wm.copy_mozcomponents_component"
    bl_label = "Copy component from active object"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        src_obj = context.active_object
        dest_objs = filter(lambda item: src_obj != item, context.selected_objects)

        mozcomponents_settings = context.scene.mozcomponents_settings
        component_class = mozcomponents_settings.registered_moz_components[self.component_name]
        component_class_name = component_class.__name__
        component_definition = mozcomponents_settings.mozcomponents_config['components'][self.component_name]

        if components.has_component(src_obj, self.component_name):
            for dest_obj in dest_objs:
                if components.has_component(dest_obj, self.component_name):
                    components.remove_component(dest_obj, self.component_name)

                components.add_component(
                    dest_obj,
                    self.component_name,
                    mozcomponents_settings.mozcomponents_config,
                    mozcomponents_settings.registered_moz_components
                )

                src_component = getattr(src_obj, component_class_name)
                dest_component = getattr(dest_obj, component_class_name)

                self.copy_type(mozcomponents_settings, src_component, dest_component, component_definition)

        return{'FINISHED'}


    def copy_type(self, mozcomponents_settings, src_obj, dest_obj, type_definition):
        for property_name, property_definition in type_definition['properties'].items():
            self.copy_property(mozcomponents_settings, src_obj, dest_obj, property_name, property_definition)

    def copy_property(self, mozcomponents_settings, src_obj, dest_obj, property_name, property_definition):
        property_type = property_definition['type']

        if property_type == 'collections':
            return

        registered_types = mozcomponents_settings.mozcomponents_config['types']
        is_custom_type = property_type in registered_types

        src_property = getattr(src_obj, property_name)
        dest_property = getattr(dest_obj, property_name)

        if is_custom_type:
            dest_obj[property_name] = self.copy_type(mozcomponents_settings, src_property, dest_property, registered_types[property_type])
        elif property_type == 'array':
            self.copy_array_property(mozcomponents_settings, src_property, dest_property, property_definition)
        else:
            setattr(dest_obj, property_name, src_property)

    def copy_array_property(self, mozcomponents_settings, src_arr, dest_arr, property_definition):
        array_type = property_definition['arrayType']
        registered_types = mozcomponents_settings.mozcomponents_config['types']
        type_definition = registered_types[array_type]

        dest_arr.clear()

        for src_item in src_arr:
            dest_item = dest_arr.add()
            self.copy_type(mozcomponents_settings, src_item, dest_item, type_definition)


class RemoveMozComponentItem(Operator):
    bl_idname = "wm.remove_mozcomponents_component_item"
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

class ReloadMozConfig(Operator):
    bl_idname = "wm.reload_mozcomponents_config"
    bl_label = "Reload Moz Config"

    def execute(self, context):
        context.scene.mozcomponents_settings.reload_config()
        context.area.tag_redraw()
        return {'FINISHED'}

class ResetMozComponentNames(Operator):
    bl_idname = "wm.reset_mozcomponents_component_names"
    bl_label = "Reset Selected Moz Component Names and Ids"

    def execute(self, context):
        for obj in context.selected_objects:
            if components.has_component(obj, "kit-piece"):
                kit_piece = obj.moz_component_kit_piece
                kit_piece.name = obj.name
                kit_piece.id = obj.name

            if components.has_component(obj, "kit-alt-materials"):
                alt_materials = obj.moz_component_kit_alt_materials
                alt_materials.name = obj.name
                alt_materials.id = obj.name

        return {'FINISHED'}

def register():
    bpy.utils.register_class(AddMozComponent)
    bpy.utils.register_class(RemoveMozComponent)
    bpy.utils.register_class(CopyMozComponent)
    bpy.utils.register_class(AddMozComponentItem)
    bpy.utils.register_class(RemoveMozComponentItem)
    bpy.utils.register_class(ReloadMozConfig)
    bpy.utils.register_class(ResetMozComponentNames)

def unregister():
    bpy.utils.unregister_class(AddMozComponent)
    bpy.utils.unregister_class(RemoveMozComponent)
    bpy.utils.unregister_class(CopyMozComponent)
    bpy.utils.unregister_class(AddMozComponentItem)
    bpy.utils.unregister_class(RemoveMozComponentItem)
    bpy.utils.unregister_class(ReloadMozConfig)
    bpy.utils.unregister_class(ResetMozComponentNames)
