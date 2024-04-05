from ...types import NodeType
from ...hubs_component import HubsComponent
from ...utils import add_component
from ....io.utils import assign_property, import_component
import bpy


class BoxCollider(HubsComponent):
    _definition = {
        'name': 'box-collider'
    }

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, blender_ob=None):
        blender_component = import_component('ammo-shape', blender_host)
        assign_property(gltf.vnodes, blender_component,
                        "type", 'box')
        assign_property(gltf.vnodes, blender_component,
                        "fit", 'manual')
        
        # These settings don't get applied when set as normal here, so use a timer to set them later.
        def set_half_extents_and_offsets():
            loc, _, scale = blender_host.matrix_world.decompose()
            blender_component.halfExtents[0] = scale[0] / 2
            blender_component.halfExtents[1] = scale[2] / 2
            blender_component.halfExtents[2] = scale[1] / 2
            blender_component.offset[0] = loc[0]
            blender_component.offset[1] = loc[2]
            blender_component.offset[2] = -loc[1]
        bpy.app.timers.register(set_half_extents_and_offsets)
