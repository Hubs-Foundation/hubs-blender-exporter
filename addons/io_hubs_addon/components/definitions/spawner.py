from bpy.props import StringProperty, BoolProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class Spawner(HubsComponent):
    _definition = {
        'name': 'spawner',
        'display_name': 'Spawner',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
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
