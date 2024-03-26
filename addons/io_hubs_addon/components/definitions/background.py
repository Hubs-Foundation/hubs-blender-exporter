from ...io.utils import import_component, set_color_from_hex
from ..hubs_component import HubsComponent
from ..types import NodeType


class Background(HubsComponent):
    _definition = {
        'name': 'background',
        'display_name': 'Background',
        'node_type': NodeType.SCENE
    }

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, blender_ob=None):
        blender_component = import_component(
            'environment-settings', blender_host)
        blender_component.toneMapping = "LinearToneMapping"
        set_color_from_hex(blender_component, "backgroundColor", component_value['color'])
