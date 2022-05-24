from bpy.props import BoolProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class Frustrum(HubsComponent):
    _definition = {
        'name': 'frustrum',
        'display_name': 'Frustrum',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'IMAGE_PLANE'
    }

    culled: BoolProperty(
        name="Culled", description="Ignore entities outside of the camera frustrum. Frustrum culling can cause problems with some animations", default=True)
