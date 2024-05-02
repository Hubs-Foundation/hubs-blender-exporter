from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType


class NetworkedTransform(HubsComponent):
    _definition = {
        'name': 'networked-transform',
        'display_name': 'Networked Transform',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'EMPTY_AXIS',
        'deps': ['networked'],
        'version': (1, 0, 0)
    }
