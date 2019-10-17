import re
import bpy
from bpy.types import Panel
from bpy.props import StringProperty
from . import components

class HubsScenePanel(Panel):
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

class HubsObjectPanel(Panel):
    bl_label = "Hubs"
    bl_idname = "OBJECT_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
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

    obj = components.get_object_source(context, panel.bl_context)

    if obj is None:
        layout.label(text="No object selected")
        return

    hubs_settings = context.scene.hubs_settings

    if hubs_settings.hubs_config is None:
        layout.label(text="No hubs config loaded")
        return

    for component_item in obj.hubs_component_list.items:
        component_name = component_item.name
        component_definition = hubs_settings.hubs_config['components'][component_name]
        component_class = hubs_settings.registered_hubs_components[component_name]
        component_class_name = component_class.__name__
        component = getattr(obj, component_class_name)

        row = layout.row()
        row.label(text=component_name)

        remove_component_operator = row.operator(
            "wm.remove_hubs_component",
            text="",
            icon="X"
        )
        remove_component_operator.component_name = component_name
        remove_component_operator.object_source = panel.bl_context

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
            elif property_type == 'array':
                array_type = property_definition['arrayType']
                array_value = getattr(component, property_name)

                col.label(text=property_name)

                for i, item in enumerate(array_value):
                    box_row = col.box().row()
                    if array_type == "materialArray":
                        nested_column = box_row.column()
                        if item.value:
                            for j, material in enumerate(item.value):
                                nested_col_row = nested_column.box().row()
                                nested_col_row.prop(data=material, property="value", text="")

                                remove_material_operator = nested_col_row.operator(
                                    "wm.remove_hubs_component_item_2d",
                                    text="",
                                    icon="X"
                                )
                                remove_material_operator.object_source = panel.bl_context
                                remove_material_operator.component_name = component_class_name
                                remove_material_operator.property_name = property_name
                                remove_material_operator.index = i
                                remove_material_operator.index2 = j

                        add_material_operator = nested_column.operator(
                            "wm.add_hubs_component_item_2d",
                            text="Add Item"
                        )
                        add_material_operator.object_source = panel.bl_context
                        add_material_operator.component_name = component_class_name
                        add_material_operator.property_name = property_name
                        add_material_operator.index = i
                    else:
                        box_row.prop(data=item, property="value", text="")

                    remove_operator = box_row.operator(
                        "wm.remove_hubs_component_item",
                        text="",
                        icon="X"
                    )
                    remove_operator.object_source = panel.bl_context
                    remove_operator.component_name = component_class_name
                    remove_operator.property_name = property_name
                    remove_operator.index = i

                add_operator = col.operator(
                    "wm.add_hubs_component_item",
                    text="Add Item"
                )
                add_operator.object_source = panel.bl_context
                add_operator.component_name = component_class_name
                add_operator.property_name = property_name

            else:
                col.prop(data=component, property=property_name)

    layout.separator()

    add_component_operator = layout.operator(
        "wm.add_hubs_component",
        text="Add Component"
    )
    add_component_operator.object_source = panel.bl_context

def register():
    bpy.utils.register_class(HubsScenePanel)
    bpy.utils.register_class(HubsObjectPanel)
    bpy.utils.register_class(HubsMaterialPanel)

def unregister():
    bpy.utils.unregister_class(HubsScenePanel)
    bpy.utils.unregister_class(HubsObjectPanel)
    bpy.utils.unregister_class(HubsMaterialPanel)
