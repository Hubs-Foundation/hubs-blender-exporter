from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions
from io_scene_gltf2.blender.exp import gltf2_blender_export
import bpy
from bpy.props import PointerProperty
from ..components.components_registry import get_components_registry
from .utils import gather_lightmap_texture_info

hubs_config = {
    "gltfExtensionName": "MOZ_hubs_components",
    "gltfExtensionVersion": 4,
}


def get_version_string():
    from .. import (bl_info)
    return str(bl_info['version'][0]) + '.' + str(bl_info['version'][1]) + '.' + str(bl_info['version'][2])


# gather_gltf_hook does not expose the info we need, make a custom hook for now
# ideally we can resolve this upstream somehow https://github.com/KhronosGroup/glTF-Blender-IO/issues/1009
orig_gather_gltf = gltf2_blender_export.__gather_gltf


def patched_gather_gltf(exporter, export_settings):
    orig_gather_gltf(exporter, export_settings)
    export_user_extensions('hubs_gather_gltf_hook',
                           export_settings, exporter._GlTF2Exporter__gltf)
    exporter._GlTF2Exporter__traverse(exporter._GlTF2Exporter__gltf.extensions)

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

        extension_name = hubs_config["gltfExtensionName"]
        gltf2_object.extensions[extension_name] = self.Extension(
            name=extension_name,
            extension={
                "version": hubs_config["gltfExtensionVersion"],
                "exporterVersion": get_version_string()
            },
            required=False
        )

        if gltf2_object.asset.extras is None:
            gltf2_object.asset.extras = {}
        gltf2_object.asset.extras["HUBS_blenderExporterVersion"] = get_version_string(
        )

    def gather_scene_hook(self, gltf2_object, blender_scene, export_settings):
        if not self.properties.enabled:
            return

        # Don't include hubs component data again in extras, even if "include custom properties" is enabled
        if gltf2_object.extras:
            for key in list(gltf2_object.extras):
                if key.startswith("hubs_"):
                    del gltf2_object.extras[key]

        self.add_hubs_components(gltf2_object, blender_scene, export_settings)

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.properties.enabled:
            return

        # Don't include hubs component data again in extras, even if "include custom properties" is enabled
        if gltf2_object.extras:
            for key in list(gltf2_object.extras):
                if key.startswith("hubs_"):
                    del gltf2_object.extras[key]

        self.add_hubs_components(gltf2_object, blender_object, export_settings)

    def gather_material_hook(self, gltf2_object, blender_material, export_settings):
        if not self.properties.enabled:
            return

        self.add_hubs_components(
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
        self.add_hubs_components(
            gltf2_object, blender_pose_bone.bone, export_settings)

    def add_hubs_components(self, gltf2_object, blender_object, export_settings):
        component_list = blender_object.hubs_component_list

        registered_hubs_components = get_components_registry()

        if component_list.items:
            extension_name = hubs_config["gltfExtensionName"]
            component_data = {}

            is_networked = False
            for component_item in component_list.items:
                component_name = component_item.name
                component_class = registered_hubs_components[component_name]
                component = getattr(blender_object, component_class.get_id())
                component_data[component_class.get_name()] = component.gather(
                    export_settings, blender_object)
                from ..components.definitions.networked import Networked
                is_networked = is_networked or Networked.get_name() in component_class.get_deps()

            # Older versions of the addon added the networked component at export time so if we open a blend file saved using a older versions the
            # component doesn't exist in the hubs_component_list and won't be exported. This patched version of gather_properties makes sure that
            # if the component has the dependency but it doesn't exist in the object, it gets exported correctly.
            if is_networked and Networked.get_name() not in component_data:
                component = getattr(blender_object, Networked.get_id())
                component_data[Networked.get_name()] = component.gather(
                    export_settings, blender_object)

            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions[extension_name] = self.Extension(
                name=extension_name,
                extension=component_data,
                required=False
            )

            self.was_used = True


class HubsComponentsExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Export Hubs Components",
        description='Include this extension in the exported glTF file.',
        default=True
    )


class HubsGLTFExportPanel(bpy.types.Panel):

    bl_idname = "HBA_PT_Export_Panel"
    bl_label = "Hubs Export Panel"
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

    def draw_header(self, context):
        props = bpy.context.scene.HubsComponentsExtensionProperties
        self.layout.prop(props, 'enabled', text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = bpy.context.scene.HubsComponentsExtensionProperties
        layout.active = props.enabled

        box = layout.box()
        box.label(text="No options yet")

# called by gltf-blender-io after it has loaded


def register_export_panel():
    try:
        bpy.utils.register_class(HubsGLTFExportPanel)
    except Exception:
        pass
    return unregister_export_panel


def unregister_export_panel():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(HubsGLTFExportPanel)
    except Exception:
        pass


def register():
    print("Register GLTF Exporter")
    register_export_panel()
    gltf2_blender_export.__gather_gltf = patched_gather_gltf
    bpy.utils.register_class(HubsComponentsExtensionProperties)
    bpy.types.Scene.HubsComponentsExtensionProperties = PointerProperty(
        type=HubsComponentsExtensionProperties)


def unregister():
    print("Unregister GLTF Exporter")
    unregister_export_panel()
    del bpy.types.Scene.HubsComponentsExtensionProperties
    bpy.utils.unregister_class(HubsComponentsExtensionProperties)
    gltf2_blender_export.__gather_gltf = orig_gather_gltf
    unregister_export_panel()
