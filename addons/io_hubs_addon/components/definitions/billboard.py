from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Billboard(HubsComponent):
    _definition = {
        'id': 'billboard',
        'name': 'hubs_component_billboard',
        'display_name': 'Billboard',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'IMAGE_PLANE'
    }

    onlyY: BoolProperty(
        name="Only Y", description="Rotate only in Y axis", default=False)
