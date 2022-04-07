import bpy
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


def update(self, context):
    context.object.hide_viewport = not bpy.context.object.hubs_component_directional_light.visible


class hubs_component_directional_light(HubsComponent):
    _definition = {
        'id': 'directional-light',
        'display_name': 'Directional Light',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'bolt.png'
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

    visible: BoolProperty(name="Visible", default=True, update=update)

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
