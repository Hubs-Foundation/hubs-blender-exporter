from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class PointLight(HubsComponent):
    _definition = {
        'name': 'point-light',
        'display_name': 'Point Light',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'LIGHT_POINT'
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
