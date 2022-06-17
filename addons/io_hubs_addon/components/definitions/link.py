from bpy.props import StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


class Link(HubsComponent):
    _definition = {
        'name': 'link',
        'display_name': 'Link',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'LINKED',
        'deps': ['networked']
    }

    href: StringProperty(name="Link URL", description="Link URL",
                         default="https://mozilla.org")

    @classmethod
    def migrate(cls, version):
        migrate_networked(cls.get_name())
