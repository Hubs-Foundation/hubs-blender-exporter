import bpy
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from .utils import HUBS_CONFIG


class glTF2ImportUserExtension:

    def __init__(self):
        self.extensions = [
            Extension(name="MOZ_hubs_components", extension={}, required=True)]
        self.properties = bpy.context.scene.hubs_import_properties

    def gather_import_scene_after_nodes_hook(self, gltf_scene, blender_scene, import_settings):
        if not self.properties.enabled:
            return

        self.add_hubs_components(gltf_scene, blender_scene, import_settings)

    def gather_import_node_after_hook(self, vnode, gltf_node, blender_object, import_settings):
        if not self.properties.enabled:
            return

        self.add_hubs_components(
            gltf_node, blender_object, import_settings)

    def gather_import_image_after_hook(self, gltf_img, blender_image, import_settings):
        # As of Blender 3.2.0 the importer doesn't import images that are not referenced by a material socket.
        # We handle this case by case in each component's gather_import override.
        pass

    def gather_import_texture_after_hook(self, gltf_texture, node_tree, mh, tex_info, location, label, color_socket, alpha_socket, is_data, import_settings):
        # As of Blender 3.2.0 the importer doesn't import textures that are not referenced by a material socket image.
        # We handle this case by case in each component's gather_import override.
        pass

    def gather_import_material_after_hook(self, gltf_material, vertex_color, blender_mat, import_settings):
        if not self.properties.enabled:
            return

        self.add_hubs_components(
            gltf_material, blender_mat, import_settings)

    def add_hubs_components(self, gltf2_object, blender_object, import_settings):
        extension_name = HUBS_CONFIG["gltfExtensionName"]
        if not gltf2_object.extensions or extension_name not in gltf2_object.extensions:
            return

        components_data = gltf2_object.extensions[extension_name]
        from ..components.components_registry import get_component_by_name
        for component_name in components_data.keys():
            component_class = get_component_by_name(component_name)
            if component_class:
                component_value = components_data[component_name]
                component_class.gather_import(
                    import_settings, blender_object, component_name, component_value)
            else:
                print('Could not import unsupported component "%s"' %
                      (component_name))


def register():
    print("Register GLTF Exporter")


def unregister():
    print("Unregister GLTF Exporter")
