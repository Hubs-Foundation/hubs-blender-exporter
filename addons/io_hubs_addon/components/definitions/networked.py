from ..hubs_component import HubsComponent
from bpy.props import StringProperty
from ..types import PanelType, NodeType
import uuid
from ..utils import add_component
from ...io.utils import import_component, assign_property
import bpy


class Networked(HubsComponent):
    _definition = {
        'name': 'networked',
        'display_name': 'Networked',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'version': (1, 0, 0)
    }

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, import_report, blender_ob=None):
        blender_component = import_component(component_name, blender_host)
        if component_value:
            for property_name, property_value in component_value.items():
                if property_name != "id":
                    # ids are generated at export time, so they shouldn't be imported.
                    assign_property(gltf.vnodes,
                                    blender_host, blender_component,
                                    property_name, property_value, import_report)

    def gather(self, export_settings, object):
        return {
            'id': str(uuid.uuid4()).upper()
        }


def migrate_networked(host):
    if Networked.get_name() not in host.hubs_component_list.items:
        add_component(host, Networked.get_name())
