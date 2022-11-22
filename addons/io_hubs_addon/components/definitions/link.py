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
        'deps': ['networked'],
        'version': (1, 0, 0)
    }

    href: StringProperty(name="Link URL", description="Link URL",
                         default="https://mozilla.org")

    def migrate(self, migration_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)

        return migration_occurred
