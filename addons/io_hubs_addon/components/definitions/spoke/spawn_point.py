from ...types import NodeType
from ...hubs_component import HubsComponent
from ...utils import add_component
from ....io.utils import assign_property, import_component


class SpawnPoint(HubsComponent):
    _definition = {
        'name': 'spawn-point'
    }

    @classmethod
    def gather_import(cls, gltf, blender_object, component_name, component_value):
        add_component(blender_object, 'waypoint')
        blender_component = import_component('waypoint', blender_object)
        assign_property(gltf.vnodes, blender_component,
                        "canBeSpawnPoint", True)
