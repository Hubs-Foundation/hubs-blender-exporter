from bpy.props import BoolProperty, StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


class Audio(HubsComponent):
    _definition = {
        'name': 'audio',
        'display_name': 'Audio',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked', 'audio-params'],
        'icon': 'OUTLINER_OB_SPEAKER'
    }

    src: StringProperty(
        name="Audio URL", description="Audio URL", default='https://mozilla.org')

    autoPlay: BoolProperty(name="Auto Play",
                           description="Auto Play",
                           default=True)

    controls: BoolProperty(
        name="Show controls",
        description="When enabled, shows play/pause, skip forward/back, and volume controls when hovering your cursor over it in Hubs",
        default=True)

    loop: BoolProperty(name="Loop",
                       description="Loop",
                       default=True)

    @classmethod
    def migrate(cls, version):
        migrate_networked(cls.get_name())
