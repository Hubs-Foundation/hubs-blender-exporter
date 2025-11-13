from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Frustrum(HubsComponent):
    _definition = {
        'name': 'frustrum',
        'display_name': 'Frustum',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'IMAGE_PLANE',
        'version': (1, 0, 0),
        'tooltip': 'Define mesh culling settings for this object',
    }

    culled: BoolProperty(
        name="Culled",
        description="Ignore entities outside of the camera frustum. Frustum culling can cause problems with some animations",
        default=True)
