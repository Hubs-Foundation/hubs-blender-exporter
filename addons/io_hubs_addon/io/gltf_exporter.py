import bpy
from .utils import HUBS_CONFIG
from bpy.props import PointerProperty
from ..components.components_registry import get_components_registry
from ..components.utils import get_host_components
import traceback

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


EXTENSION_NAME = HUBS_CONFIG["gltfExtensionName"]
EXTENSION_VERSION = HUBS_CONFIG["gltfExtensionVersion"]


def get_version_string():
    from .. import (bl_info)
    return str(bl_info['version'][0]) + '.' + str(bl_info['version'][1]) + '.' + str(bl_info['version'][2])
    #  or (shorter):
    info = bl_info['version']
    return f"{info[0]}.{info[1]}.{info[2]}"
    #  or (faster):
    return '.'.join(map(str, bl_info['version']))


def export_callback(callback_method, export_settings):
    # Note: we loop through copied lists of the potential component hosts
    # to allow the callbacks to change the host names.  This is needed
    # because a name change will cause Blender to update the host lists in
    # mid iteration and so multiple callbacks could be executed for the same
    # component/host.

    for scene in bpy.data.scenes[:]:  # I don't think we need to copy the dicts [:], since we can't even alter the list, this would save mem
        for component in get_host_components(scene):
            component_callback = getattr(component, callback_method)
            try:
                component_callback(export_settings, scene)
            except Exception:
                traceback.print_exc()

    for ob in bpy.data.objects[:]:
        for component in get_host_components(ob):
            component_callback = getattr(component, callback_method)
            try:
                component_callback(export_settings, ob, ob)
            except Exception:
                traceback.print_exc()

        if ob.type == 'ARMATURE':
            for bone in ob.data.bones[:]:
                for component in get_host_components(bone):
                    component_callback = getattr(component, callback_method)
                    try:
                        component_callback(export_settings, bone, ob)
                    except Exception:
                        traceback.print_exc()

    for material in bpy.data.materials[:]:
        for component in get_host_components(material):
            component_callback = getattr(component, callback_method)
            try:
                component_callback(export_settings, material)
            except Exception:
                traceback.print_exc()


def glTF2_pre_export_callback(export_settings):
    from io_scene_gltf2.blender.com.gltf2_blender_extras import BLACK_LIST
    BLACK_LIST.extend(glTF2ExportUserExtension.EXCLUDED_PROPERTIES)
    export_callback("pre_export", export_settings)


def glTF2_post_export_callback(export_settings):
    export_callback("post_export", export_settings)

    from io_scene_gltf2.blender.com.gltf2_blender_extras import BLACK_LIST
    for excluded_prop in glTF2ExportUserExtension.EXCLUDED_PROPERTIES:
        if excluded_prop in BLACK_LIST:
            BLACK_LIST.remove(excluded_prop)


# This class name is specifically looked for by gltf-blender-io and it's hooks are automatically invoked on export


class glTF2ExportUserExtension:

    EXCLUDED_PROPERTIES = []

    @classmethod
    def add_excluded_property(cls, key):
        if key not in glTF2ExportUserExtension.EXCLUDED_PROPERTIES:
            glTF2ExportUserExtension.EXCLUDED_PROPERTIES.append(key)

    @classmethod
    def remove_excluded_property(cls, key):
        if key in glTF2ExportUserExtension.EXCLUDED_PROPERTIES:
            glTF2ExportUserExtension.EXCLUDED_PROPERTIES.remove(key)

    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension

        self.Extension = Extension
        self.properties = bpy.context.scene.HubsComponentsExtensionProperties
        self.was_used = False
        self.delayed_gathers = []

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

        self.export_hubs_components(gltf2_object, blender_scene, export_settings)
        self.call_delayed_gathers()

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.properties.enabled:
            return

        self.export_hubs_components(gltf2_object, blender_object, export_settings)

    def gather_material_hook(self, gltf2_object, blender_material, export_settings):
        if not self.properties.enabled:
            return

        self.export_hubs_components(
            gltf2_object, blender_material, export_settings)

        from .utils import gather_lightmap_texture_info
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

    def call_delayed_gathers(self):
        for delayed_gather in self.delayed_gathers:
            component_data, component_name, gather = delayed_gather
            component_data[component_name] = gather()
        self.delayed_gathers.clear()

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
                    data = component.gather(export_settings, blender_object)
                    if hasattr(data, "delayed_gather"):
                        self.delayed_gathers.append(
                            (component_data, component_class.gather_name(), data))
                    else:
                        component_data[component_class.gather_name()] = data
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


class HubsComponentsExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Export Hubs Components",
        description='Include this extension in the exported glTF file',
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


def register():
    print("Register glTF Exporter")
    if bpy.app.version < (3, 0, 0):
        gltf2_blender_export.__gather_gltf = patched_gather_gltf
    bpy.utils.register_class(HubsComponentsExtensionProperties)
    bpy.types.Scene.HubsComponentsExtensionProperties = PointerProperty(
        type=HubsComponentsExtensionProperties)
    glTF2ExportUserExtension.add_excluded_property("HubsComponentsExtensionProperties")


def unregister():
    print("Unregister glTF Exporter")
    del bpy.types.Scene.HubsComponentsExtensionProperties
    bpy.utils.unregister_class(HubsComponentsExtensionProperties)
    if bpy.app.version < (3, 0, 0):
        gltf2_blender_export.__gather_gltf = orig_gather_gltf
    glTF2ExportUserExtension.remove_excluded_property("HubsComponentsExtensionProperties")
