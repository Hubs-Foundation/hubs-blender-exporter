from ...types import NodeType
from ...hubs_component import HubsComponent
from ...utils import add_component
from ....io.utils import assign_property, import_component


class BoxCollider(HubsComponent):
    _definition = {
        'name': 'box-collider'
    }

    @classmethod
    def gather_import(cls, gltf, blender_object, component_name, component_value):
        add_component(blender_object, 'ammo-shape')
        blender_component = import_component('ammo-shape', blender_object)
        assign_property(gltf.vnodes, blender_component,
                        "type", 'box')
