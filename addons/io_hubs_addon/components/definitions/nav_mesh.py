from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class NavMesh(HubsComponent):
    _definition = {
        'name': 'nav-mesh',
        'display_name': 'Navigation Mesh',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'GRID',
        'version': (1, 0, 0)
    }

    @classmethod
    def poll(cls, panel_type, host, ob=None):
        return host.type == 'MESH'
