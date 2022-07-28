from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, PointerProperty
from bpy.types import Image
from ...io.utils import add_hubs_import_component, assign_property, gather_texture_property, gather_color_property
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
import bpy
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage


TOME_MAPPING = [("NoToneMapping", "None", "No tone mapping."),
                ("LinearToneMapping", "Linear", "Linear tone mapping"),
                ("ReinhardToneMapping", "ThreeJS 'Reinhard'",
                 "ThreeJS 'Reinhard' tone mapping"),
                ("CineonToneMapping", "ThreeJS 'Cineon'",
                 "ThreeJS 'Cineon' tone mapping"),
                ("ACESFilmicToneMapping", "ThreeJS 'ACES Filmic'",
                 "ThreeJS 'ACES Filmic' tone mapping"),
                ("LUTToneMapping", "Blender 'Filmic'", "Match Blender's Filmic tone mapping")]


class EnvironmentSettings(HubsComponent):
    _definition = {
        'name': 'environment-settings',
        'display_name': 'Environment Settings',
        'category': Category.SCENE,
        'node_type': NodeType.SCENE,
        'panel_type': [PanelType.SCENE],
        'icon': 'WORLD'
    }

    toneMapping: EnumProperty(
        name="Tone Mapping",
        description="Tone Mapping",
        items=TOME_MAPPING,
        default="LUTToneMapping")

    toneMappingExposure: FloatProperty(
        name="Exposure", description="Exposure level of tone mapping", default=1.0, min=0.0, soft_min=0.0)

    backgroundColor: FloatVectorProperty(name="Background Color",
                                         description="Background Color",
                                         subtype='COLOR',
                                         default=(1.0, 1.0, 1.0, 1.0),
                                         size=4,
                                         min=0,
                                         max=1)
    backgroundTexture: PointerProperty(
        name="Background Image",
        description="An equirectangular image to use as the scene background",
        type=Image
    )

    envMapTexture: PointerProperty(
        name="EnvMap",
        description="An equirectangular image to use as the default environment map for all objects",
        type=Image
    )

    def gather(self, export_settings, object):
        return {
            'toneMapping': self.toneMapping,
            'toneMappingExposure': self.toneMappingExposure,
            'backgroundColor': gather_color_property(export_settings, object, self, 'backgroundColor'),
            'backgroundTexture': gather_texture_property(
                export_settings,
                object,
                self,
                'backgroundTexture'),
            'envMapTexture': gather_texture_property(
                export_settings,
                object,
                self,
                'envMapTexture')
        }

    @classmethod
    def gather_import(cls, import_settings, blender_object, component_name, component_value):
        blender_component = add_hubs_import_component(
            component_name, blender_object)

        images = {}
        for gltf_texture in import_settings.data.textures:
            extensions = gltf_texture.extensions
            source = None
            if extensions:
                MOZ_texture_rgbe = extensions.get('MOZ_texture_rgbe')
                if MOZ_texture_rgbe:
                    source = MOZ_texture_rgbe['source']
            else:
                source = gltf_texture.source

            if source is not None and source not in import_settings.data.images:
                BlenderImage.create(
                    import_settings, source)
                pyimg = import_settings.data.images[source]
                blender_image_name = pyimg.blender_image_name
                images[source] = blender_image_name

        for property_name, property_value in component_value.items():
            if isinstance(property_value, dict) and property_value['__mhc_link_type'] == "texture":
                blender_image_name = images[property_value['index']]
                blender_image = bpy.data.images[blender_image_name]
                setattr(blender_component, property_name, blender_image)

            else:
                assign_property(import_settings.vnodes, blender_component,
                                property_name, property_value)
