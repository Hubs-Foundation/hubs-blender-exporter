from bpy.props import FloatVectorProperty, FloatProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class AmbientLight(HubsComponent):
    _definition = {
        'name': 'ambient-light',
        'display_name': 'Ambient Light',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'LIGHT_HEMI'
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
