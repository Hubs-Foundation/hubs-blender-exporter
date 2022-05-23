import bpy
from bpy.props import FloatVectorProperty, FloatProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class AmbientLight(HubsComponent):
    _definition = {
        'id': 'ambient-light',
        'name': 'hubs_component_ambient_light',
        'display_name': 'Ambient Light',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
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
