from bpy.props import FloatProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class ScaleAudioFeedback(HubsComponent):
    _definition = {
        'name': 'scale-audio-feedback',
        'display_name': 'Scale Audio Feedback',
        'category': Category.AVATAR,
        'node_type': Node,
        'panel_type': PanelType.OBJECT
    }

    minScale: FloatProperty(name="Min Scale",
                            description="Min Scale",
                            default=1.0)

    maxScale: FloatProperty(name="Max Scale",
                            description="Max Scale",
                            default=1.5)
