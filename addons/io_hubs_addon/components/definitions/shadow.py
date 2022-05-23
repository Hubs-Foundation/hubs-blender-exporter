from bpy.props import BoolProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class Shadow(HubsComponent):
    _definition = {
        'name': 'shadow',
        'display_name': 'Shadow',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'MOD_MASK'
    }

    cast: BoolProperty(
        name="Cast Shadow", description="Cast shadow", default=True)

    receive: BoolProperty(
        name="Receive Shadow", description="Receive shadow", default=True)
