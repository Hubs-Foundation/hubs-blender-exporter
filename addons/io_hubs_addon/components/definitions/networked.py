from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
import uuid


class Networked(HubsComponent):
    _definition = {
        'id': 'networked',
        'name': 'hubs_component_networked',
        'display_name': 'Networked',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'dep_only': True
    }

    def gather(self, export_settings, object):
        return {
            'id': str(uuid.uuid4()).upper()
        }
