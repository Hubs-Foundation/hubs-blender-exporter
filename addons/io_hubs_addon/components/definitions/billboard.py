from bpy.props import BoolProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class Billboard(HubsComponent):
    _definition = {
        'name': 'billboard',
        'display_name': 'Billboard',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'IMAGE_PLANE'
    }

    onlyY: BoolProperty(
        name="Only Y", description="Rotate only in Y axis", default=False)
