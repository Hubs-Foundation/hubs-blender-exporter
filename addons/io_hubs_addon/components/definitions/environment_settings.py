from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, PointerProperty, BoolProperty
from bpy.types import Image
from ...io.utils import import_component, assign_property, gather_texture_property, gather_color_property
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
import bpy
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage


TOME_MAPPING = [("NoToneMapping", "None", "No tone mapping"),
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
        name="Exposure", description="Exposure level of tone mapping", default=1.0, min=0.0)

    backgroundColor: FloatVectorProperty(name="Background Color",
                                         description="Background Color",
                                         subtype='COLOR_GAMMA',
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

    enableHDRPipeline: BoolProperty(
        name="Enable HDR Pipeline",
        description="Enable the new (experimental) HDR render pipeline with post processing effects and modified lighting + tonemapping model. NOTE: This checkbox is an opt-in to breaking changes. New versions of the Hubs client may break scenes with this option checked without warning and may reqquire re-export with a later Blender exporter.",
        default=False
    )

    enableBloom: BoolProperty(
        name="Bloom",
        description="Add a Bloom effect to bright objects.",
        default=False
    )
    bloomThreshold: FloatProperty(
        name="Threshold", description="Values brighter than this in the final render (before tone mapping) will have bloom applied to them. The threshold is applied starting at 1, so a value of 0 will cover all 'HDR' values. You can specify a number below 0 to have bloom effect SDR values (not recommended)", default=1.0, min=0.0, soft_min=1.0)
    bloomIntensity: FloatProperty(
        name="Intensity", description="Scales the intensity of the bloom effect", default=1.0, min=0.0)
    bloomRadius: FloatProperty(
        name="Radius", description="Spread distance of the bloom effect", default=0.6, min=0.0, soft_max=1.0)
    bloomSmoothing: FloatProperty(
        name="Smoothing", description="Makes transition between under/over-threshold more gradual.", default=0.025, min=0.0, soft_max=1.0)

    def draw(self, context, layout, panel):
        layout.prop(data=self, property="enableHDRPipeline")

        layout.prop(data=self, property="backgroundColor")
        layout.prop(data=self, property="backgroundTexture")
        layout.prop(data=self, property="envMapTexture")

        layout.prop(data=self, property="toneMapping")
        layout.prop(data=self, property="toneMappingExposure")

        if self.enableHDRPipeline:
            layout = layout.box()
            top_row = layout.row()
            top_row.prop(data=self, property="enableBloom")
            if self.enableBloom:
                layout.prop(data=self, property="bloomThreshold")
                layout.prop(data=self, property="bloomIntensity")
                layout.prop(data=self, property="bloomRadius")
                layout.prop(data=self, property="bloomSmoothing")

    def gather(self, export_settings, object):
        output = {
            'toneMapping': self.toneMapping,
            'toneMappingExposure': self.toneMappingExposure,
            'backgroundColor': gather_color_property(export_settings, object, self, 'backgroundColor', 'COLOR_GAMMA'),
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

        if self.enableHDRPipeline:
            output["enableHDRPipeline"] = True
            if self.enableBloom:
                output["enableBloom"] = True
                output["bloom"] = {
                    "threshold": self.bloomThreshold,
                    "intensity": self.bloomIntensity,
                    "radius": self.bloomRadius,
                    "smoothing": self.bloomSmoothing,
                }

        return output

    @classmethod
    def gather_import(cls, import_settings, blender_object, component_name, component_value):
        blender_component = import_component(
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
