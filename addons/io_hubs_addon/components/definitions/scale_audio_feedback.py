from bpy.props import FloatProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class ScaleAudioFeedback(HubsComponent):
    _definition = {
        'name': 'scale-audio-feedback',
        'display_name': 'Scale Audio Feedback',
        'category': Category.AVATAR,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'GRAPH',
        'version': (1, 0, 0)
    }

    minScale: FloatProperty(name="Min Scale",
                            description="Min Scale",
                            default=1.0)

    maxScale: FloatProperty(name="Max Scale",
                            description="Max Scale",
                            default=1.5)
