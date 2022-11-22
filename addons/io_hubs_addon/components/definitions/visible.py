import bpy
from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType

class Visible(HubsComponent):
    _definition = {
        'name': 'visible',
        'display_name': 'Visible',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'HIDE_OFF',
        'version': (1, 0, 0)
    }

    visible: BoolProperty(name="Visible", default=True)
