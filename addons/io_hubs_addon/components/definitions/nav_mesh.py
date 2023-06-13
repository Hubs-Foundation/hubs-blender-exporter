from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import has_component, add_component


class NavMesh(HubsComponent):
    _definition = {
        'name': 'nav-mesh',
        'display_name': 'Navigation Mesh',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'GRID',
        'version': (1, 0, 1),
        'deps': ['visible']
    }

    @classmethod
    def poll(cls, panel_type, host, ob=None):
        return host.type == 'MESH'

    @classmethod
    def init(cls, obj):
        obj.hubs_component_visible.visible = False
        obj.hubs_component_list.items.get('visible').isDependency = True

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 1):
            if not has_component(host, 'visible'):
                add_component(host, 'visible')
                host.hubs_component_visible.visible = False
                migration_occurred = True

        return migration_occurred
