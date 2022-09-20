from bpy.props import FloatVectorProperty, FloatProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class HemisphereLight(HubsComponent):
    _definition = {
        'name': 'hemisphere-light',
        'display_name': 'Hemisphere Light',
        'category': Category.LIGHTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'LIGHT_AREA'
    }

    skyColor: FloatVectorProperty(name="Sky Color",
                                  description="Sky Color",
                                  subtype='COLOR_GAMMA',
                                  default=(1.0, 1.0, 1.0, 1.0),
                                  size=4,
                                  min=0,
                                  max=1)

    groundColor: FloatVectorProperty(name="Ground Color",
                                     description="Ground Color",
                                     subtype='COLOR_GAMMA',
                                     default=(1.0, 1.0, 1.0, 1.0),
                                     size=4,
                                     min=0,
                                     max=1)

    intensity: FloatProperty(name="Intensity",
                             description="Intensity",
                             default=1.0)
