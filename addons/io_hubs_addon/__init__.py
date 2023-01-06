from . import preferences
from .io import gltf_exporter, gltf_importer
from . import (nodes, components)
from .io import gltf_exporter
import bpy

bl_info = {
    "name": "Hubs Blender Addon",
    "author": "Mozilla Hubs",
    "description": "Tools for developing glTF assets for Mozilla Hubs",
    "blender": (3, 1, 2),
    "version": (1, 0, 0),
    "location": "",
    "wiki_url": "https://github.com/MozillaReality/hubs-blender-exporter",
    "tracker_url": "https://github.com/MozillaReality/hubs-blender-exporter/issues",
    "support": "COMMUNITY",
    "warning": "",
    "category": "Generic"
}


def register():
    preferences.register()
    nodes.register()
    components.register()
    gltf_importer.register()
    gltf_exporter.register()

    # Migrate components if the add-on is enabled in the middle of a session.
    if bpy.context.preferences.is_dirty:
        def registration_migration():
            # Passing True as the first argument of the operator forces an undo step to be created.
            bpy.ops.wm.migrate_hubs_components(
                True, is_registration=True)
        bpy.app.timers.register(registration_migration)


def unregister():
    gltf_exporter.unregister()
    gltf_importer.unregister()
    components.unregister()
    nodes.unregister()
    preferences.unregister()


# called by gltf-blender-io after it has loaded

glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension
glTF2_pre_export_callback = gltf_exporter.glTF2_pre_export_callback
glTF2_post_export_callback = gltf_exporter.glTF2_post_export_callback
if bpy.app.version > (3, 0, 0):
    glTF2ImportUserExtension = gltf_importer.glTF2ImportUserExtension


def register_panel():
    return gltf_exporter.register_export_panel()
