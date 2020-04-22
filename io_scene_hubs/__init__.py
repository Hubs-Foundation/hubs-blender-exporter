import bpy

from . import settings
from . import components
from . import operators
from . import panels
from .gather_properties import gather_properties

bl_info = {
    "name" : "io_scene_hubs",
    "author" : "Robert Long",
    "description" : "",
    "blender" : (2, 82, 0),
    "version" : (0, 0, 2),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

# Monkey patch to add gather_gltf_hook, must be removed once handled upstream https://github.com/KhronosGroup/glTF-Blender-IO/issues/1009
from io_scene_gltf2.blender.exp import gltf2_blender_export
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions
orig_gather_gltf = gltf2_blender_export.__gather_gltf
def patched_gather_gltf(exporter, export_settings):
    orig_gather_gltf(exporter, export_settings)
    export_user_extensions('gather_gltf_hook', export_settings, exporter._GlTF2Exporter__gltf)
    exporter._GlTF2Exporter__traverse(exporter._GlTF2Exporter__gltf.extensions)

# Monkey patch to add gather_joint_hook, must be removed once handled upstream
from io_scene_gltf2.blender.exp import gltf2_blender_gather_joints
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions
orig_gather_joint = gltf2_blender_gather_joints.gather_joint
def patched_gather_joint(blender_bone, export_settings):
    node = orig_gather_joint(blender_bone, export_settings)
    export_user_extensions('gather_joint_hook', export_settings, node, blender_bone)
    return node

def register():
    gltf2_blender_export.__gather_gltf = patched_gather_gltf
    gltf2_blender_gather_joints.gather_joint = patched_gather_joint

    components.register()
    settings.register()
    operators.register()
    panels.register()


def unregister():
    gltf2_blender_export.__gather_gltf = orig_gather_gltf
    gltf2_blender_gather_joints.gather_joint = orig_gather_joint

    components.unregister()
    settings.unregister()
    operators.unregister()
    panels.unregister()

    unregister_export_panel()

if __name__ == "__main__":
    register()

# called by gltf-blender-io after it has loaded
def register_panel():
    try:
        bpy.utils.register_class(panels.HubsGLTFExportPanel)
    except Exception:
        pass
    return unregister_export_panel

def unregister_export_panel():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(panels.HubsGLTFExportPanel)
    except Exception:
        pass

# This class name is specifically looked for by gltf-blender-io and it's hooks are automatically invoked on export
class glTF2ExportUserExtension:
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.properties = bpy.context.scene.HubsComponentsExtensionProperties
        self.hubs_settings = bpy.context.scene.hubs_settings

    def gather_gltf_hook(self, gltf2_object, export_settings):
        if not self.properties.enabled: return

        hubs_config = self.hubs_settings.hubs_config
        extension_name = hubs_config["gltfExtensionName"]
        gltf2_object.extensions[extension_name] = self.Extension(
            name=extension_name,
            extension={
                "version": hubs_config["gltfExtensionVersion"]
            },
            required=False
        )

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.properties.enabled: return

        self.add_hubs_components(gltf2_object, blender_object, export_settings)

    def gather_material_hook(self, gltf2_object, blender_material, export_settings):
        if not self.properties.enabled: return

        self.add_hubs_components(gltf2_object, blender_material, export_settings)

    def gather_joint_hook(self, gltf2_object, blender_pose_bone, export_settings):
        if not self.properties.enabled: return

        self.add_hubs_components(gltf2_object, blender_pose_bone.bone, export_settings)

    def add_hubs_components(self, gltf2_object, blender_object, export_settings):
        component_list = blender_object.hubs_component_list

        hubs_config = self.hubs_settings.hubs_config
        registered_hubs_components = self.hubs_settings.registered_hubs_components

        if component_list.items:
            extension_name = hubs_config["gltfExtensionName"]
            component_data = {}

            for component_item in component_list.items:
                component_name = component_item.name
                component_definition = hubs_config['components'][component_name]
                component_class = registered_hubs_components[component_name]
                component_class_name = component_class.__name__
                component = getattr(blender_object, component_class_name)
                component_data[component_name] = gather_properties(export_settings, blender_object, component, component_definition, hubs_config)

            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions[extension_name] = self.Extension(
                name=extension_name,
                extension=component_data,
                required=False
            )
