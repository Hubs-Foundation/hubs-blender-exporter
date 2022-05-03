import bpy
from bpy.props import BoolProperty, FloatProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class AmbientLight(HubsComponent):
    _definition = {
        'id': 'personal-space-invader',
        'name': 'hubs_component_personal_space_invader',
        'display_name': 'Personal Space Invader',
        'category': Category.AVATAR,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'MATSHADERBALL'
    }

    radius: FloatProperty(name="Radius",
                          description="Radius",
                          default=0.1)

    useMaterial: BoolProperty(name="Use Material",
                              description="Use Material",
                              default=False)

    invadingOpacity: FloatProperty(name="Invading Opacity",
                                   description="Invading Opacity",
                                   default=0.3)
