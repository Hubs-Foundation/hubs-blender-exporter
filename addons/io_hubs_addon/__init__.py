from .utils import create_prefs_dir
import sys
import bpy
from .io import gltf_exporter, gltf_importer, panels
from . import (nodes, components)
from . import preferences
from . import third_party
from . import debugger
from . import icons
bl_info = {
    "name": "Hubs Blender Addon",
    "author": "The Hubs Community",
    "description": "Tools for developing glTF assets for Hubs",
    "blender": (3, 1, 2),
    "version": (1, 8, 0, "dev_build"),
    "location": "",
    "wiki_url": "https://github.com/Hubs-Foundation/hubs-blender-exporter",
    "tracker_url": "https://github.com/Hubs-Foundation/hubs-blender-exporter/issues",
    "support": "COMMUNITY",
    "warning": "",
    "category": "Generic"
}


create_prefs_dir()


# Blender 4.2+ glTF Extension Import/Export Settings Panels
def draw_import_settings(context, layout):
    layout_header, layout_body = layout.panel('HBA_PT_Import_Panel', default_closed=True)

    # Panel Header
    props = bpy.context.scene.HubsComponentsExtensionImportProperties
    layout_header.use_property_split = False
    layout_header.prop(props, 'enabled', text="")
    layout_header.label(text="Hubs Components")

    # Panel Body
    if layout_body:
        gltf_importer.HubsGLTFImportPanel.draw_body(context, layout_body)


def draw_export_settings(context, layout):
    layout_header, layout_body = layout.panel('HBA_PT_Export_Panel', default_closed=True)

    # Panel Header
    props = bpy.context.scene.HubsComponentsExtensionProperties
    layout_header.use_property_split = False
    layout_header.prop(props, 'enabled', text="")
    layout_header.label(text="Hubs Components")

    # Panel Body
    if layout_body:
        gltf_exporter.HubsGLTFExportPanel.draw_body(context, layout_body)


def register():
    icons.register()
    preferences.register()
    nodes.register()
    components.register()
    gltf_importer.register()
    gltf_exporter.register()
    panels.register_panels()
    third_party.register()
    debugger.register()

    # Register the glTF Extension Import and Export Settings Panels in Blender 4.2+
    if bpy.app.version >= (4, 2, 0):
        from io_scene_gltf2 import (
            exporter_extension_layout_draw,
            importer_extension_layout_draw
        )
        importer_extension_layout_draw[bl_info["name"]] = draw_import_settings
        exporter_extension_layout_draw[bl_info["name"]] = draw_export_settings

    # Migrate components if the add-on is enabled in the middle of a session.
    if bpy.context.preferences.is_dirty:
        def registration_migration():
            # Passing True as the first argument of the operator forces an undo step to be created.
            bpy.ops.wm.migrate_hubs_components(
                'EXEC_DEFAULT', True, is_registration=True)
        bpy.app.timers.register(registration_migration)


def unregister():
    third_party.unregister()
    panels.unregister_panels()
    gltf_exporter.unregister()
    gltf_importer.unregister()
    components.unregister()
    nodes.unregister()
    preferences.unregister()
    debugger.unregister()
    icons.unregister()

    # Unregister the glTF Extension Import and Export Settings Panels in Blender 4.2+
    if bpy.app.version >= (4, 2, 0):
        from io_scene_gltf2 import (
            exporter_extension_layout_draw,
            importer_extension_layout_draw
        )
        del exporter_extension_layout_draw[bl_info["name"]]
        del importer_extension_layout_draw[bl_info["name"]]


# called by gltf-blender-io after it has loaded


glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension
glTF2_pre_export_callback = gltf_exporter.glTF2_pre_export_callback
glTF2_post_export_callback = gltf_exporter.glTF2_post_export_callback
if bpy.app.version > (3, 0, 0):
    glTF2ImportUserExtension = gltf_importer.glTF2ImportUserExtension


def register_panel():
    return panels.register_panels()
