from .io import gltf_exporter
from . import (nodes, components, gizmos)
bl_info = {
    "name": "New Hubs Blender Addon",
    "author": "Mozilla Hubs",
    "description": "Tools for developing GLTF assets for Mozilla Hubs",
    "blender": (2, 92, 0),
    "version": (0, 0, 11),
    "location": "",
    "wiki_url": "https://github.com/MozillaReality/hubs-blender-exporter",
    "tracker_url": "https://github.com/MozillaReality/hubs-blender-exporter/issues",
    "support": "COMMUNITY",
    "warning": "",
    "category": "Generic"
}

# TODO Support architecture kit?


def register():
    print('Register Addon')

    gltf_exporter.register()
    nodes.register()
    gizmos.register()
    components.register()


def unregister():
    components.unregister()
    gizmos.unregister()
    nodes.unregister()
    gltf_exporter.unregister()

    print('Addon unregistered')


# called by gltf-blender-io after it has loaded


glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension


def register_panel():
    return gltf_exporter.register_export_panel()
