from ...io.utils import import_component, assign_property
from ..hubs_component import HubsComponent
from ..types import NodeType


class EnvironmentSettings(HubsComponent):
    _definition = {
        'name': 'background',
        'display_name': 'Background',
        'node_type': NodeType.SCENE
    }

    @classmethod
    def gather_import(cls, import_settings, blender_object, component_name, component_value):
        blender_component = import_component(
            'environemnt-settings', blender_object)
        for property_name, property_value in component_value.items():
            assign_property(import_settings.vnodes, blender_component,
                            property_name, property_value)
