from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Shadow(HubsComponent):
    _definition = {
        'id': 'shadow',
        'name': 'hubs_component_shadow',
        'display_name': 'Shadow',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'MOD_MASK'
    }

    cast: BoolProperty(
        name="Cast Shadow", description="Cast shadow", default=True)

    receive: BoolProperty(
        name="Receive Shadow", description="Receive shadow", default=True)
