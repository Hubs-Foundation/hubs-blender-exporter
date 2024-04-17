from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType


class Billboard(HubsComponent):
    _definition = {
        'name': 'billboard',
        'display_name': 'Billboard',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'IMAGE_PLANE',
        'version': (1, 0, 0)
    }

    onlyY: BoolProperty(
        name="Vertical Axis Only",
        description="Locks the Vertical Axis to enable only side to side movement in world space and removes any other rotational transforms",
        default=False)
