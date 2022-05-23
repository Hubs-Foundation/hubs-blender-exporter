from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class SpotLight(HubsComponent):
    _definition = {
        'id': 'spot-light',
        'name': 'hubs_component_spot_light',
        'display_name': 'Spot Light',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'LIGHT_SPOT'
    }

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    intensity: FloatProperty(name="Intensity",
                             description="Intensity",
                             default=1.0)

    range: FloatProperty(name="Range",
                         description="Range",
                         default=1.0)

    decay: FloatProperty(name="Decay",
                         description="Decay",
                         default=1.0)

    innerConeAngle: FloatProperty(
        name="Cone Inner Angle",
        description="A double value describing the angle, in degrees, of a cone inside of which there will be no volume reduction.",
        subtype="ANGLE",
        default=0.0,
        min=0.0,
        soft_min=0.0,
        max=1.57079632679,
        soft_max=1.57079632679)

    outerConeAngle: FloatProperty(
        name="Cone Outer Angle",
        description="A double value describing the angle, in degrees, of a cone outside of which the volume will be reduced by a constant value, defined by the coneOuterGain attribute.",
        subtype="ANGLE",
        default=0.78539816339,
        min=0.0005729577951408,
        soft_min=0.0005729577951408,
        max=1.57079632679,
        soft_max=1.57079632679)

    decay: FloatProperty(name="Decay",
                         description="Decay",
                         default=1.0)

    castShadow: BoolProperty(
        name="Cast Shadow", description="Cast Shadow", default=True)

    shadowMapResolution: IntVectorProperty(name="Shadow Map Resolution",
                                           description="Shadow Map Resolution",
                                           size=2,
                                           subtype='COORDINATES',
                                           default=[512, 512])

    shadowBias: FloatProperty(name="Shadow Bias",
                              description="Shadow Bias",
                              default=1.0)

    shadowRadius: FloatProperty(name="Shadow Radius",
                                description="Shadow Radius",
                                default=1.0)
