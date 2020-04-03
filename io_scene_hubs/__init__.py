import bpy

from . import settings
from . import components
from . import operators
from . import panels

bl_info = {
    "name" : "io_scene_hubs",
    "author" : "Robert Long",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

def register():
    print("register")
    components.register()
    settings.register()
    operators.register()
    panels.register()

    bpy.utils.register_class(ExampleExtensionProperties)
    bpy.types.Scene.ExampleExtensionProperties = bpy.props.PointerProperty(type=ExampleExtensionProperties)

def unregister():
    components.unregister()
    settings.unregister()
    operators.unregister()
    panels.unregister()

    unregister_panel()
    bpy.utils.unregister_class(ExampleExtensionProperties)
    del bpy.types.Scene.ExampleExtensionProperties

if __name__ == "__main__":
    register()

class ExampleExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Export Hubs Components",
        description='Include this extension in the exported glTF file.',
        default=True
        )
    float_property: bpy.props.FloatProperty(
        name='Sample FloatProperty',
        description='This is an example of a FloatProperty used by a UserExtension.',
        default=1.0
        )


# called by gltf-blender-io after it has loaded
def register_panel():
    # Register the panel on demand, we need to be sure to only register it once
    # This is necessary because the panel is a child of the extensions panel,
    # which may not be registered when we try to register this extension
    try:
        bpy.utils.register_class(GLTF_PT_UserExtensionPanel)
    except Exception:
        pass

    # If the glTF exporter is disabled, we need to unregister the extension panel
    # Just return a function to the exporter so it can unregister the panel
    return unregister_panel


def unregister_panel():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(GLTF_PT_UserExtensionPanel)
    except Exception:
        pass

class GLTF_PT_UserExtensionPanel(bpy.types.Panel):

    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Hubs Components"
    bl_parent_id = "GLTF_PT_export_user_extensions"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    # def draw_header(self, context):
    #     props = bpy.context.scene.ExampleExtensionProperties
    #     self.layout.prop(props, 'enabled')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = bpy.context.scene.ExampleExtensionProperties
        layout.active = props.enabled

        # box = layout.box()
        # box.label(text=glTF_extension_name)

        props = bpy.context.scene.ExampleExtensionProperties
        layout.prop(props, 'float_property', text="Some float value")


import logging

log = logging.getLogger(__name__)
from . import exporter

class glTF2ExportUserExtension:

    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension, ChildOfRootExtension
        self.Extension = Extension
        self.ChildOfRootExtension = ChildOfRootExtension
        self.properties = bpy.context.scene.ExampleExtensionProperties
        self.hubs_settings = bpy.context.scene.hubs_settings
        print("settings", self.hubs_settings)

    # def gather_scene_hook(self, gltf2_object, blender_object, export_settings):
    #     print("gather_scene_hook")
    #     extension_name = self.hubs_settings.hubs_config["gltfExtensionName"]
    #         print("adding root extension")
    #         if gltf2_object.extensions is None:
    #             gltf2_object.extensions = {}

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        print("gather_node_hook")
        self.add_hubs_components(gltf2_object, blender_object, export_settings)

    def gather_material_hook(self, gltf2_object, blender_object, export_settings):
        print("gather_material_hook")
        self.add_hubs_components(gltf2_object, blender_object, export_settings)

    def add_hubs_components(self, gltf2_object, blender_object, export_settings):
        component_list = blender_object.hubs_component_list

        hubs_config = self.hubs_settings.hubs_config
        registered_hubs_components = self.hubs_settings.registered_hubs_components

        print("add_hubs_components", blender_object, component_list)

        if component_list.items:
            print("has components")
            extension_name = hubs_config["gltfExtensionName"]
            component_data = {}

            for component_item in component_list.items:
                component_name = component_item.name
                component_definition = hubs_config['components'][component_name]
                component_class = registered_hubs_components[component_name]
                component_class_name = component_class.__name__
                component = getattr(blender_object, component_class_name)
                component_data[component_name] = exporter.gather_properties(export_settings, blender_object, component, component_definition, hubs_config)

            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions[extension_name] = self.Extension(
                name=extension_name,
                extension=component_data,
                required=False
            )

            print(component_data, gltf2_object)
