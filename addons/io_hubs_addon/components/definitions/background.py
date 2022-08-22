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
        blender_component.toneMapping = "LinearToneMapping"
        set_color_from_hex(blender_component, "backgroundColor", component_value['color'])
