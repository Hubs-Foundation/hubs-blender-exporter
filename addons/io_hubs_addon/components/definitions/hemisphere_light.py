from bpy.props import FloatVectorProperty, FloatProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class HemisphereLight(HubsComponent):
    _definition = {
        'name': 'hemisphere-light',
        'display_name': 'Hemisphere Light',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'LIGHT_AREA'
    }

    skyColor: FloatVectorProperty(name="Sky Color",
                               description="Sky Color",
                               subtype='COLOR',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    groundColor: FloatVectorProperty(name="Ground Color",
                               description="Ground Color",
                               subtype='COLOR',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    intensity: FloatProperty(name="Intensity",
                             description="Intensity",
                             default=1.0)
