from .hubs_component import HubsComponent
from bpy.props import StringProperty
from ..types import Category, PanelType, NodeType
import uuid


class Networked(HubsComponent):
    _definition = {
        'id': 'networked',
        'name': 'hubs_component_networked',
        'display_name': 'Networked',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'dep_only': True
    }

    id: StringProperty(
        name="Network ID",
        description="Network ID",
        default=str(uuid.uuid4()).upper()
    )

    def draw(self, context, layout):
        layout.label(text="Network ID:")
        layout.label(text=self.id)
