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
        name="Model Source", description="The web address (URL) of the glTF to be spawned", default="https://mozilla.org")

    applyGravity: BoolProperty(
        name="Apply Gravity", description="Apply gravity to spawned object", default=False)

    def gather(self, export_settings, object):
        return {
            'src': self.src,
            'mediaOptions': {
                'applyGravity': self.applyGravity
            }
        }

    def migrate(self, version, host, migration_report, ob=None):
        if version < (1, 0, 0):
            self.applyGravity = self[
                'mediaOptions']['applyGravity']
