from bpy.props import StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


class Model(HubsComponent):
    _definition = {
        'name': 'model',
        'display_name': 'Model',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'SCENE_DATA',
        'deps': ['networked'],
        'version': (1, 0, 0)
    }

    src: StringProperty(name="Model URL", description="Model URL",
                        default="https://mozilla.org")

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)

        return migration_occurred
