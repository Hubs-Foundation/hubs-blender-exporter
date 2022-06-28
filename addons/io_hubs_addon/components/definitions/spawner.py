import bpy
from bpy.props import StringProperty, BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Spawner(HubsComponent):
    _definition = {
        'name': 'spawner',
        'display_name': 'Spawner',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MOD_PARTICLE_INSTANCE'
    }

    src: StringProperty(
        name="URL", description="Source image URL", default="https://mozilla.org")

    applyGravity: BoolProperty(
        name="Apply Gravity", description="Apply gravity to spawned object", default=False)

    def gather(self, export_settings, object):
        return {
            'src': self.src,
            'mediaOptions': {
                'applyGravity': self.applyGravity
            }
        }

    @classmethod
    def migrate(cls, version):
        if version < (1, 0, 0):
            def migrate_data(ob):
                if cls.get_name() in ob.hubs_component_list.items:
                    ob.hubs_component_spawner.applyGravity = ob.hubs_component_spawner[
                        'mediaOptions']['applyGravity']

            for ob in bpy.data.objects:
                migrate_data(ob)

                if ob.type == 'ARMATURE':
                    for bone in ob.data.bones:
                        migrate_data(bone)
