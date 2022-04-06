import bpy
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from .hubs_component import HubsComponent
from ..types import PanelType, NodeType


class hubs_component_point_light(HubsComponent):
    _definition = {
        'export_name': 'point-light',
        'display_name': 'Point Light',
        'category': 'Elements',
        'node_type': NodeType.NODE,
        'pane_type': PanelType.OBJECT,
        'icon': 'point-light.png'
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
