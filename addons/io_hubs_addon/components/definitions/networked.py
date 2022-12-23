from ..hubs_component import HubsComponent
from bpy.props import StringProperty
from ..types import PanelType, NodeType
import uuid
from ..utils import add_component
import bpy


class Networked(HubsComponent):
    _definition = {
        'name': 'networked',
        'display_name': 'Networked',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'version': (1, 0, 0)
    }

    def gather(self, export_settings, object):
        return {
            'id': str(uuid.uuid4()).upper()
        }


def migrate_networked(host):
    if Networked.get_name() not in host.hubs_component_list.items:
        add_component(host, Networked.get_name())
