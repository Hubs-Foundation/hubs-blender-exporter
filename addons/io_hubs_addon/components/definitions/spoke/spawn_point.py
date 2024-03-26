from ...types import NodeType
from ...hubs_component import HubsComponent
from ...utils import add_component
from ....io.utils import assign_property, import_component


class SpawnPoint(HubsComponent):
    _definition = {
        'name': 'spawn-point'
    }

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, blender_ob=None):
        add_component(blender_host, 'waypoint')
        blender_component = import_component('waypoint', blender_host)
        assign_property(gltf.vnodes, blender_component,
                        "canBeSpawnPoint", True)
