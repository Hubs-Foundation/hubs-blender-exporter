from bpy.props import StringProperty, BoolProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Spawner(HubsComponent):
    _definition = {
        'id': 'spawner',
        'name': 'hubs_component_spawner',
        'display_name': 'Spawner',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'MOD_PARTICLE_INSTANCE'
    }

    src: StringProperty(
        name="URL", description="Source image URL", default="https://")

    applyGravity: BoolProperty(
        name="Apply Gravity", description="Apply gravity to spawned object", default=False)
