import bpy
from ..components.components_registry import get_components_registry
from .utils import gather_lightmap_texture_info, HUBS_CONFIG


EXTENSION_NAME = HUBS_CONFIG["gltfExtensionName"]
EXTENSION_VERSION = HUBS_CONFIG["gltfExtensionVersion"]

if bpy.app.version < (3, 0, 0):
    from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions
    from io_scene_gltf2.blender.exp import gltf2_blender_export

    # gather_gltf_hook does not expose the info we need, make a custom hook for now
    # ideally we can resolve this upstream somehow https://github.com/KhronosGroup/glTF-Blender-IO/issues/1009
    orig_gather_gltf = gltf2_blender_export.__gather_gltf


def patched_gather_gltf(exporter, export_settings):
    orig_gather_gltf(exporter, export_settings)
    export_user_extensions('hubs_gather_gltf_hook',
                           export_settings, exporter._GlTF2Exporter__gltf)
    exporter._GlTF2Exporter__traverse(exporter._GlTF2Exporter__gltf.extensions)


def get_version_string():
    from .. import (bl_info)
    return str(bl_info['version'][0]) + '.' + str(bl_info['version'][1]) + '.' + str(bl_info['version'][2])


def glTF2_pre_export_callback(export_settings):
    for ob in bpy.context.view_layer.objects:
        component_list = ob.hubs_component_list

        registered_hubs_components = get_components_registry()

        if component_list.items:
            for component_item in component_list.items:
                component_name = component_item.name
                if component_name in registered_hubs_components:
                    component_class = registered_hubs_components[component_name]
                    component = getattr(ob, component_class.get_id())
                    component.pre_export(export_settings, ob)


def glTF2_post_export_callback(export_settings):
    for ob in bpy.context.view_layer.objects:
        component_list = ob.hubs_component_list

        registered_hubs_components = get_components_registry()

        if component_list.items:
            for component_item in component_list.items:
                component_name = component_item.name
                if component_name in registered_hubs_components:
                    component_class = registered_hubs_components[component_name]
                    component = getattr(ob, component_class.get_id())
                    component.post_export(export_settings, ob)


# This class name is specifically looked for by gltf-blender-io and it's hooks are automatically invoked on export


class glTF2ExportUserExtension:
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension

        self.Extension = Extension
        self.properties = bpy.context.scene.HubsComponentsExtensionProperties
        self.was_used = False

    def hubs_gather_gltf_hook(self, gltf2_object, export_settings):
        if not self.properties.enabled or not self.was_used:
            return

        extension_name = EXTENSION_NAME
        gltf2_object.extensions[extension_name] = self.Extension(
            name=extension_name,
            extension={
                "version": EXTENSION_VERSION,
                "exporterVersion": get_version_string()
            },
            required=False
        )

        if gltf2_object.asset.extras is None:
            gltf2_object.asset.extras = {}
        gltf2_object.asset.extras["HUBS_blenderExporterVersion"] = get_version_string(
        )
        gltf2_object.asset.extras["gltf_yup"] = export_settings['gltf_yup']

    def gather_gltf_extensions_hook(self, gltf2_plan, export_settings):
        self.hubs_gather_gltf_hook(gltf2_plan, export_settings)

    def gather_scene_hook(self, gltf2_object, blender_scene, export_settings):
        if not self.properties.enabled:
            return

        # Don't include hubs component data again in extras, even if "include custom properties" is enabled
        if gltf2_object.extras:
            for key in list(gltf2_object.extras):
                if key.startswith("hubs_"):
                    del gltf2_object.extras[key]

        self.export_hubs_components(
            gltf2_object, blender_scene, export_settings)

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.properties.enabled:
            return

        # Don't include hubs component data again in extras, even if "include custom properties" is enabled
        if gltf2_object.extras:
            for key in list(gltf2_object.extras):
                if key.startswith("hubs_"):
                    del gltf2_object.extras[key]

        self.export_hubs_components(
            gltf2_object, blender_object, export_settings)

    def gather_material_hook(self, gltf2_object, blender_material, export_settings):
        if not self.properties.enabled:
            return

        self.export_hubs_components(
            gltf2_object, blender_material, export_settings)

        if blender_material.node_tree and blender_material.use_nodes:
            lightmap_texture_info = gather_lightmap_texture_info(
                blender_material, export_settings)
            if lightmap_texture_info:
                gltf2_object.extensions["MOZ_lightmap"] = self.Extension(
                    name="MOZ_lightmap",
                    extension=lightmap_texture_info,
                    required=False,
                )

    def gather_material_unlit_hook(self, gltf2_object, blender_material, export_settings):
        self.gather_material_hook(
            gltf2_object, blender_material, export_settings)

    def gather_joint_hook(self, gltf2_object, blender_pose_bone, export_settings):
        if not self.properties.enabled:
            return
        self.export_hubs_components(
            gltf2_object, blender_pose_bone.bone, export_settings)

    def export_hubs_components(self, gltf2_object, blender_object, export_settings):
        component_list = blender_object.hubs_component_list

        registered_hubs_components = get_components_registry()

        if component_list.items:
            extension_name = EXTENSION_NAME
            component_data = {}

            for component_item in component_list.items:
                component_name = component_item.name
                if component_name in registered_hubs_components:
                    component_class = registered_hubs_components[component_name]
                    component = getattr(
                        blender_object, component_class.get_id())
                    component_data[component_class.get_name()] = component.gather(
                        export_settings, blender_object)
                else:
                    print('Could not export unsupported component "%s"' %
                          (component_name))

            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions[extension_name] = self.Extension(
                name=extension_name,
                extension=component_data,
                required=False
            )

            self.was_used = True


def register():
    print("Register GLTF Exporter")
    if bpy.app.version < (3, 0, 0):
        gltf2_blender_export.__gather_gltf = patched_gather_gltf

def unregister():
    print("Unregister GLTF Exporter")
    if bpy.app.version < (3, 0, 0):
        gltf2_blender_export.__gather_gltf = orig_gather_gltf
