import re
import bpy
from bpy.types import Panel
from bpy.props import StringProperty
from . import components

class MozComponentsScenePanel(Panel):
    bl_label = 'Moz Components'
    bl_idname = "SCENE_PT_mozcomponents"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene.mozcomponents_settings,
                 "config_path", text="Config File")
        row.operator("wm.reload_mozcomponents_config", text="", icon="FILE_REFRESH")

        draw_components_list(self, context)

class MozComponentsObjectPanel(Panel):
    bl_label = "Moz Components"
    bl_idname = "OBJECT_PT_mozcomponents"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        draw_components_list(self, context)

class MozComponentsMaterialPanel(Panel):
    bl_label = 'Moz Components'
    bl_idname = "MATERIAL_PT_mozcomponents"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        draw_components_list(self, context)

class MozComponentsGLTFExportPanel(bpy.types.Panel):

    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "MOZ Components"
    bl_parent_id = "GLTF_PT_export_user_extensions"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        props = bpy.context.scene.MozComponentsExtensionProperties
        self.layout.prop(props, 'enabled', text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = bpy.context.scene.MozComponentsExtensionProperties
        layout.active = props.enabled

        box = layout.box()
        box.label(text="No options yet")



def draw_components_list(panel, context):
    layout = panel.layout

    obj = components.get_object_source(context, panel.bl_context)

    if obj is None:
        layout.label(text="No object selected")
        return

    mozcomponents_settings = context.scene.mozcomponents_settings

    if mozcomponents_settings.mozcomponents_config is None:
        layout.label(text="No mozcomponents config loaded")
        return

    for component_item in obj.mozcomponents_component_list.items:
        row = layout.row()
        draw_component(panel, context, obj, row, component_item)

    layout.separator()

    add_component_operator = layout.operator(
        "wm.add_mozcomponents_component",
        text="Add Component"
    )
    add_component_operator.object_source = panel.bl_context

def draw_component(panel, context, obj, row, component_item):
    mozcomponents_settings = context.scene.mozcomponents_settings

    component_name = component_item.name
    component_definition = mozcomponents_settings.mozcomponents_config['components'][component_name]
    component_class = mozcomponents_settings.registered_moz_components[component_name]
    component_class_name = component_class.__name__
    component = getattr(obj, component_class_name)

    col = row.column()
    top_row = col.row()
    top_row.label(text=component_name)

    copy_component_operator = top_row.operator(
        "wm.copy_mozcomponents_component",
        text="Copy"
    )
    copy_component_operator.component_name = component_name

    remove_component_operator = top_row.operator(
        "wm.remove_mozcomponents_component",
        text="",
        icon="X"
    )
    remove_component_operator.component_name = component_name
    remove_component_operator.object_source = panel.bl_context

    content_col = col.column()

    path = panel.bl_context + "." + component_class_name

    draw_type(context, content_col, obj, component, path, component_definition)

def draw_type(context, col, obj, target, path, type_definition):
    for property_name, property_definition in type_definition['properties'].items():
        draw_property(context, col, obj, target, path, property_name, property_definition)

def draw_property(context, col, obj, target, path, property_name, property_definition):
    property_type = property_definition['type']
    mozcomponents_settings = context.scene.mozcomponents_settings
    registered_types = mozcomponents_settings.mozcomponents_config['types']
    is_custom_type = property_type in registered_types

    if property_type == 'collections':
        draw_collections_property(context, col, obj, target, path, property_name, property_definition)
    elif property_type == 'array':
        draw_array_property(context, col, obj, target, path, property_name, property_definition)
    elif is_custom_type:
        draw_type(context, col, obj, target, path, registered_types[property_type])
    else:
        col.prop(data=target, property=property_name)

def draw_collections_property(_context, col, obj, _target, _path, property_name, property_definition):
    collections_row = col.row()
    collections_row.label(text=property_name)

    filtered_collection_names = []
    collection_prefix_regex = None

    if 'collectionPrefix' in property_definition:
        collection_prefix = property_definition['collectionPrefix']
        collection_prefix_regex = re.compile(
            r'^' + collection_prefix)

    for collection in obj.users_collection:
        if collection_prefix_regex and collection_prefix_regex.match(collection.name):
            new_name = collection_prefix_regex.sub(
                "", collection.name)
            filtered_collection_names.append(new_name)
        elif not collection_prefix_regex:
            filtered_collection_names.append(collection.name)

    collections_row.box().label(text=", ".join(filtered_collection_names))

def draw_array_property(context, col, obj, target, path, property_name, property_definition):
    mozcomponents_settings = context.scene.mozcomponents_settings
    registered_types = mozcomponents_settings.mozcomponents_config['types']
    array_type = property_definition['arrayType']
    item_definition = registered_types[array_type]

    array_value = getattr(target, property_name)

    property_path = path + "." + property_name

    if property_name != 'value':
        col.label(text=property_name)

    for i, item in enumerate(array_value):
        box_row = col.box().row()
        box_col = box_row.column()
        item_path = property_path + "." + str(i)

        draw_type(context, box_col, obj, item, item_path, item_definition)

        remove_operator = box_row.column().operator(
            "wm.remove_mozcomponents_component_item",
            text="",
            icon="X"
        )
        remove_operator.path = item_path

    add_operator = col.operator(
        "wm.add_mozcomponents_component_item",
        text="Add Item"
    )
    add_operator.path = property_path

def register():
    bpy.utils.register_class(MozComponentsScenePanel)
    bpy.utils.register_class(MozComponentsObjectPanel)
    bpy.utils.register_class(MozComponentsMaterialPanel)

def unregister():
    bpy.utils.unregister_class(MozComponentsScenePanel)
    bpy.utils.unregister_class(MozComponentsObjectPanel)
    bpy.utils.unregister_class(MozComponentsMaterialPanel)
