from . import (nodes, components)
from .io import gltf_exporter, gltf_importer, panels
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
    panels.register()
    gltf_exporter.register()
    gltf_importer.register()
    nodes.register()
    components.register()


def unregister():
    components.unregister()
    nodes.unregister()
    gltf_importer.unregister()
    gltf_exporter.unregister()
    panels.unregister()


# called by gltf-blender-io after it has loaded

glTF2ExportUserExtension = gltf_exporter.glTF2ExportUserExtension
glTF2_pre_export_callback = gltf_exporter.glTF2_pre_export_callback
glTF2_post_export_callback = gltf_exporter.glTF2_post_export_callback
if bpy.app.version > (3, 0, 0):
    glTF2ImportUserExtension = gltf_importer.glTF2ImportUserExtension


def register_panel():
    return panels.register_panels()
