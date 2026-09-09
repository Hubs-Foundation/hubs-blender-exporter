from ...hubs_component import HubsComponent
from ...types import Category, PanelType, NodeType


class Trimesh(HubsComponent):
    _definition = {
        'name': 'trimesh',
        'display_name': 'Trimesh',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'MESH_DATA',
        'version': (1, 0, 0)
    }
