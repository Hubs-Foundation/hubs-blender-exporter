import re
import bpy
from bpy.types import Panel, Menu

class AddHubsSceneComponentMenu(Menu):
    bl_label = "Add Hubs Component to Scene"
    bl_idname = "SCENE_MT_add_hubs_scene_component_menu"

    def draw(self, context):
        layout = self.layout

        hubs_components = bpy.context.scene.hubs_settings.registered_hubs_components

        for component_name, component_class in hubs_components.items():
            if component_class.is_scene_component:
                operator = layout.operator(
                    "wm.add_hubs_scene_component",
                    text=component_name
                )
                operator.component_name = component_name

class AddHubsObjectComponentMenu(Menu):
    bl_label = "Add Hubs Component to Object"
    bl_idname = "OBJECT_MT_add_hubs_object_component_menu"

    def draw(self, context):
        layout = self.layout

        hubs_components = bpy.context.scene.hubs_settings.registered_hubs_components

        for component_name, component_class in hubs_components.items():
            if component_class.is_node_component:
                operator = layout.operator(
                    "wm.add_hubs_object_component",
                    text=component_name
                )
                operator.component_name = component_name

class AddHubsMaterialComponentMenu(Menu):
    bl_label = "Add Hubs Component to Material"
    bl_idname = "MATERIAL_MT_add_hubs_material_component_menu"

    def draw(self, context):
        layout = self.layout

        hubs_components = bpy.context.scene.hubs_settings.registered_hubs_components

        for component_name, component_class in hubs_components.items():
            if component_class.is_material_component:
                operator = layout.operator(
                    "wm.add_hubs_material_component",
                    text=component_name
                )
                operator.component_name = component_name

class HubsObjectPanel(Panel):
    bl_label = "Hubs"
    bl_idname = "OBJECT_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        draw_components_list(self, context)


class HubsSettingsPanel(Panel):
    bl_label = 'Hubs'
    bl_idname = "SCENE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene.hubs_settings,
                 "config_path", text="Config File")
        row.operator("wm.reload_hubs_config", text="", icon="FILE_REFRESH")

        row = layout.row()
        row.operator("wm.export_hubs_gltf", text="Export Scene")
        row.operator("wm.export_hubs_gltf",
                     text="Export Selected").selected = True

        draw_components_list(self, context)

class HubsMaterialPanel(Panel):
    bl_label = 'Hubs'
    bl_idname = "MATERIAL_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        draw_components_list(self, context)

def draw_components_list(panel, context):
    layout = panel.layout

    if panel.bl_context == 'scene':
        obj = context.scene
    elif panel.bl_context == 'material':
        obj = context.material
    else:
        obj = context.object

    hubs_settings = context.scene.hubs_settings

    if hubs_settings.hubs_config is None:
        return

    for component_item in obj.hubs_component_list.items:
        component_name = component_item.name
        component_definition = hubs_settings.hubs_config['components'][component_name]
        component_class = hubs_settings.registered_hubs_components[component_name]
        component_class_name = component_class.__name__
        component = getattr(obj, component_class_name)

        row = layout.row()
        row.label(text=component_name)

        if panel.bl_context == 'scene':
            remove_component_operator = "wm.remove_hubs_scene_component"
        elif panel.bl_context == 'material':
            remove_component_operator = "wm.remove_hubs_material_component"
        else:
            remove_component_operator = "wm.remove_hubs_object_component"

        row.operator(
            remove_component_operator,
            text="",
            icon="X"
        ).component_name = component_name

        split = layout.split(factor=0.1)
        col = split.column()
        col.label(text=" ")
        col = split.column()
        for property_name, property_definition in component_definition['properties'].items():
            property_type = property_definition['type']
            if property_type == 'collections':
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

            else:
                col.prop(data=component, property=property_name)

    layout.separator()

    menu = layout.operator(
        "wm.call_menu",
        text="Add Component"
    )

    if panel.bl_context == 'scene':
        menu.name = "SCENE_MT_add_hubs_scene_component_menu"
    elif panel.bl_context == 'material':
        menu.name = "MATERIAL_MT_add_hubs_material_component_menu"
    else:
        menu.name = "OBJECT_MT_add_hubs_object_component_menu"

def register():
    bpy.utils.register_class(AddHubsObjectComponentMenu)
    bpy.utils.register_class(AddHubsSceneComponentMenu)
    bpy.utils.register_class(AddHubsMaterialComponentMenu)
    bpy.utils.register_class(HubsObjectPanel)
    bpy.utils.register_class(HubsSettingsPanel)
    bpy.utils.register_class(HubsMaterialPanel)

def unregister():
    bpy.utils.unregister_class(AddHubsSceneComponentMenu)
    bpy.utils.unregister_class(AddHubsMaterialComponentMenu)
    bpy.utils.unregister_class(AddHubsObjectComponentMenu)
    bpy.utils.unregister_class(HubsObjectPanel)
    bpy.utils.unregister_class(HubsSettingsPanel)
    bpy.utils.unregister_class(HubsMaterialPanel)
