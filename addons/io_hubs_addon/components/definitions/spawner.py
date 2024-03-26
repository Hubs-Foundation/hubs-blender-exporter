import bpy
from bpy.props import StringProperty, BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ...io.utils import import_component, assign_property


class Spawner(HubsComponent):
    _definition = {
        'name': 'spawner',
        'display_name': 'Spawner',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MOD_PARTICLE_INSTANCE',
        'version': (1, 0, 0)
    }

    src: StringProperty(
        name="Model Source", description="The web address (URL) of the glTF to be spawned",
        default="https://mozilla.org")

    applyGravity: BoolProperty(
        name="Apply Gravity", description="Apply gravity to spawned object", default=False)

    def gather(self, export_settings, object):
        return {
            'src': self.src,
            'mediaOptions': {
                'applyGravity': self.applyGravity
            }
        }

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            try:
                self.applyGravity = self[
                    'mediaOptions']['applyGravity']
            except Exception:  # applyGravity was never saved, so it must have been left on the default value: False.
                self.applyGravity = False

        return migration_occurred

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, blender_ob=None):
        blender_component = import_component(
            component_name, blender_host)

        for property_name, property_value in component_value.items():
            if property_name == 'mediaOptions':
                setattr(blender_component, "applyGravity",
                        property_value["applyGravity"])
            else:
                assign_property(gltf.vnodes, blender_component,
                                property_name, property_value)
