from .io import gltf_exporter
from .gizmos import (gizmo_registry, gizmo_group)
from . import (settings, components, elements, ui)
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


def register():
    print('Register Addon')

    gltf_exporter.register()

    settings.register()
    gizmo_registry.register()
    gizmo_group.register()
    components.register()
    elements.register()
    ui.register()


def unregister():
    print('Unregister Addon')

    ui.unregister()
    elements.unregister()
    components.unregister()
    gizmo_group.unregister()
    gizmo_registry.unregister()
    settings.unregister()

    gltf_exporter.unregister()


# called by gltf-blender-io after it has loaded


glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension


def register_panel():
    return gltf_exporter.register_panel()
