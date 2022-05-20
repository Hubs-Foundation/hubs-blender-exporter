from bpy.props import BoolProperty, StringProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Audio(HubsComponent):
    _definition = {
        'id': 'audio',
        'name': 'hubs_component_audio',
        'display_name': 'Audio',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'deps': ['networked', 'audio-params'],
        'icon': 'OUTLINER_OB_SPEAKER'
    }

    src: StringProperty(
        name="Audio URL", description="Audio URL", default='https://mozilla.org')

    autoPlay: BoolProperty(name="Auto Play",
                           description="Auto Play",
                           default=True)

    controls: BoolProperty(name="Show controls",
                           description="Show Controls",
                           default=True)

    loop: BoolProperty(name="Loop",
                       description="Loop",
                       default=True)
