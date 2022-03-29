from .io import gltf_exporter
from .gizmos import (gizmo_registry, gizmo_group)
from . import (settings, components, prefabs, ui)
bl_info = {
    "name" : "Hubs Blender Exporter",
    "author" : "MozillaReality",
    "description" : "Tools for developing GLTF assets for Mozilla Hubs",
    "blender" : (2, 93, 4),
    "version" : (0, 0, 15),
    "location" : "",
    "wiki_url": "https://github.com/MozillaReality/hubs-blender-exporter",
    "tracker_url": "https://github.com/MozillaReality/hubs-blender-exporter/issues",
    "support": "COMMUNITY",
    "warning": "",
    "category": "Generic"
}


def register():
    print('Register Addon')

    gltf_exporter.register()

    settings.register()
    gizmo_registry.register()
    gizmo_group.register()
    components.register()
    prefabs.register()
    ui.register()


def unregister():
    print('Unregister Addon')

    ui.unregister()
    prefabs.unregister()
    components.unregister()
    gizmo_group.unregister()
    gizmo_registry.unregister()
    settings.unregister()

    gltf_exporter.unregister()


# called by gltf-blender-io after it has loaded


glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension


def register_panel():
    return gltf_exporter.register_panel()
