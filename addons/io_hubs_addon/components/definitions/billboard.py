from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType


class Billboard(HubsComponent):
    _definition = {
        'name': 'billboard',
        'display_name': 'Billboard',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'IMAGE_PLANE'
    }

    onlyY: BoolProperty(
        name="Only Y", description="Rotate only in Y axis", default=False)
