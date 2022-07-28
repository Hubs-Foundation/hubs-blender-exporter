import bpy
from bpy.props import PointerProperty, IntVectorProperty, BoolProperty


class HubsComponentsExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Export Hubs Components",
        description='Include this extension in the exported glTF file',
        default=True
    )
    version: IntVectorProperty(size=3)


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


class HubsGLTFImportPanel(bpy.types.Panel):

    bl_idname = "HBA_PT_Import_Panel"
    bl_label = "Hubs Import Panel"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Hubs Components"
    bl_parent_id = "GLTF_PT_import_user_extensions"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "IMPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        props = bpy.context.scene.hubs_import_properties
        self.layout.prop(props, 'enabled', text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = bpy.context.scene.hubs_import_properties
        layout.active = props.enabled

        box = layout.box()
        box.label(text="No options yet")


class HubsImportProperties(bpy.types.PropertyGroup):
    enabled: BoolProperty(
        name="Import Hubs Components",
        description='Import Hubs components from the glTF file',
        default=True
    )

# called by gltf-blender-io after it has loaded


def register_panels():
    try:
        bpy.utils.register_class(HubsGLTFExportPanel)
        bpy.utils.register_class(HubsGLTFImportPanel)
    except Exception:
        pass
    return unregister_panels


def unregister_panels():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(HubsGLTFImportPanel)
        bpy.utils.unregister_class(HubsGLTFExportPanel)
    except Exception:
        pass


def register():
    register_panels()
    bpy.utils.register_class(HubsComponentsExtensionProperties)
    bpy.types.Scene.HubsComponentsExtensionProperties = PointerProperty(
        type=HubsComponentsExtensionProperties)
    bpy.utils.register_class(HubsImportProperties)
    bpy.types.Scene.hubs_import_properties = PointerProperty(
        type=HubsImportProperties)


def unregister():
    del bpy.types.Scene.HubsComponentsExtensionProperties
    bpy.utils.unregister_class(HubsComponentsExtensionProperties)
    del bpy.types.Scene.hubs_import_properties
    bpy.utils.unregister_class(HubsImportProperties)
    unregister_panels()
