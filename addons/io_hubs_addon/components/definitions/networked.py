from ..hubs_component import HubsComponent
from bpy.props import StringProperty
from ..types import Category, PanelType, NodeType
import uuid


class Networked(HubsComponent):
    _definition = {
        'name': 'networked',
        'display_name': 'Networked',
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT
    }

    id: StringProperty(
        name="Network ID",
        description="Network ID",
        default=str(uuid.uuid4()).upper()
    )

    def draw(self, context, layout):
        layout.label(text="Network ID:")
        layout.label(text=self.id)
