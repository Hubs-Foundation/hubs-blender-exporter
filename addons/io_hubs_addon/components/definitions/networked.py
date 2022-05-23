from ..hubs_component import HubsComponent
from bpy.props import StringProperty
from bpy.types import Node
from ..types import PanelType
import uuid


class Networked(HubsComponent):
    _definition = {
        'name': 'networked',
        'display_name': 'Networked',
        'node_type': Node,
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
