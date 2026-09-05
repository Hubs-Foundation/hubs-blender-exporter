import bpy

from .gltf_exporter import HubsGLTFExportPanel
from .gltf_importer import HubsGLTFImportPanel


def register_panels():
    # Blender 4.2+ uses the glTF extension draw callback instead of
    # the legacy GLTF_PT_*_user_extensions parent panels.
    if bpy.app.version >= (4, 2, 0):
        return unregister_panels

    try:
        bpy.utils.register_class(HubsGLTFExportPanel)
        bpy.utils.register_class(HubsGLTFImportPanel)
    except Exception:
        pass

    return unregister_panels


def unregister_panels():
    if bpy.app.version >= (4, 2, 0):
        return

    # Since panels are registered on demand, it is possible they are not registered.
    try:
        bpy.utils.unregister_class(HubsGLTFImportPanel)
        bpy.utils.unregister_class(HubsGLTFExportPanel)
    except Exception:
        pass
