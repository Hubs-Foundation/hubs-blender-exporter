from bpy.props import BoolProperty, StringProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType
from .networked import migrate_networked


class Audio(HubsComponent):
    _definition = {
        'name': 'audio',
        'display_name': 'Audio',
        'category': Category.ELEMENTS,
        'node_type': Node,
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

    @classmethod
    def migrate(cls):
        migrate_networked(cls.get_name())
