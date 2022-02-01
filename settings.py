import bpy
from bpy.props import StringProperty, PointerProperty, CollectionProperty
from bpy.types import PropertyGroup

hba_config = {
    "configVersion": 1,
    "gltfExtensionName": "MOZ_hubs_components",
    "gltfExtensionVersion": 3,
}


class HubsSettings(PropertyGroup):
    output_path: StringProperty(
        name="output_path",
        description="Output path for the GLB file",
        default="./output.glb",
        options={'HIDDEN'},
        maxlen=1024,
        subtype='FILE_PATH',
        # update=config_updated
    )

    config_path: StringProperty(
        name="config_path",
        description="Config path",
        default="",
        options={'HIDDEN'},
        maxlen=1024,
        subtype='FILE_PATH'
    )

    @ property
    def hba_config(self):
        global hba_config
        return hba_config


def register():
    bpy.utils.register_class(HubsSettings)
    bpy.types.Scene.hba_settings = PointerProperty(type=HubsSettings)


def unregister():
    bpy.utils.unregister_class(HubsSettings)
    del bpy.types.Scene.hba_settings
