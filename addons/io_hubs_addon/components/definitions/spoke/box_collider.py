from ...types import NodeType
from ...hubs_component import HubsComponent
from ...utils import add_component
from ....io.utils import assign_property, import_component


class BoxCollider(HubsComponent):
    _definition = {
        'name': 'box-collider'
    }

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, blender_ob=None):
        blender_component = import_component('ammo-shape', blender_host)
        assign_property(gltf.vnodes, blender_component,
                        "type", 'box')
