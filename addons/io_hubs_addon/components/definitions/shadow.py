from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType


class Shadow(HubsComponent):
    _definition = {
        'name': 'shadow',
        'display_name': 'Shadow',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'MOD_MASK',
        'version': (1, 0, 0)
    }

    cast: BoolProperty(
        name="Cast Shadow", description="Cast shadow", default=True)

    receive: BoolProperty(
        name="Receive Shadow", description="Receive shadow", default=True)
