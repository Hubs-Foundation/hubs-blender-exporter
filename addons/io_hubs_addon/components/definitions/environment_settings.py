from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, PointerProperty
from bpy.types import Image
from ...io.utils import gather_texture_property, gather_color_property
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


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
        'panel_type': PanelType.SCENE,
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
