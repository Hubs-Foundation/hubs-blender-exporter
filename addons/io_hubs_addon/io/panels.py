import bpy
from .gltf_exporter import HubsGLTFExportPanel
from .gltf_importer import HubsGLTFImportPanel


def register_panels():
    try:
        bpy.utils.register_class(HubsGLTFExportPanel)
        bpy.utils.register_class(HubsGLTFImportPanel)
    except Exception:
        pass
    return unregister_panels


def unregister_panels():
    # Since panels are registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(HubsGLTFImportPanel)
        bpy.utils.unregister_class(HubsGLTFExportPanel)
    except Exception:
        pass

