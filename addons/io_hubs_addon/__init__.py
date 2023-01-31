from .utils import get_user_python_path
import sys
import bpy
from .io import gltf_exporter
from . import (nodes, components)
from . import preferences
from . import third_party
from . import preferences, ws_server
bl_info = {
    "name": "Hubs Blender Addon",
    "author": "Mozilla Hubs",
    "description": "Tools for developing GLTF assets for Mozilla Hubs",
    "blender": (3, 1, 2),
    "version": (1, 2, 1, "dev_build"),
    "location": "",
    "wiki_url": "https://github.com/MozillaReality/hubs-blender-exporter",
    "tracker_url": "https://github.com/MozillaReality/hubs-blender-exporter/issues",
    "support": "COMMUNITY",
    "warning": "",
    "category": "Generic"
}

sys.path.insert(0, get_user_python_path())


def register():
    preferences.register()
    nodes.register()
    components.register()
    gltf_exporter.register()
    third_party.register()
    ws_server.register()

    # Migrate components if the add-on is enabled in the middle of a session.
    if bpy.context.preferences.is_dirty:
        def registration_migration():
            # Passing True as the first argument of the operator forces an undo step to be created.
            bpy.ops.wm.migrate_hubs_components(
                True, is_registration=True)
        bpy.app.timers.register(registration_migration)


def unregister():
    third_party.unregister()
    ws_server.unregister()
    gltf_exporter.unregister()
    components.unregister()
    nodes.unregister()
    preferences.unregister()


# called by gltf-blender-io after it has loaded


glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension
glTF2_pre_export_callback = gltf_exporter.glTF2_pre_export_callback
glTF2_post_export_callback = gltf_exporter.glTF2_post_export_callback


def register_panel():
    return gltf_exporter.register_export_panel()
