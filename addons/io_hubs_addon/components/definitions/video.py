from bpy.props import BoolProperty, EnumProperty, StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..consts import PROJECTION_MODE
from .networked import migrate_networked


class Video(HubsComponent):
    _definition = {
        'name': 'video',
        'display_name': 'Video',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked', 'audio-params'],
        'icon': 'FILE_MOVIE'
    }

    src: StringProperty(
        name="Video URL", description="The web address of the video", default='https://mozilla.org')

    projection: EnumProperty(
        name="Projection",
        description="Projection",
        items=PROJECTION_MODE,
        default="flat")

    autoPlay: BoolProperty(name="Auto Play",
                           description="Auto Play",
                           default=True)

    controls: BoolProperty(name="Show controls",
                           description="When enabled, shows play/pause, skip forward/back, and, if the video contains audio, volume controls when hovering your cursor over it in Hubs",
                           default=True)

    loop: BoolProperty(name="Loop",
                       description="Loop",
                       default=True)

    def migrate(self, migration_type, version, host, migration_report, ob=None):
        migrate_networked(host)
