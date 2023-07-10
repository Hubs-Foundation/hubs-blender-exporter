from bpy.props import BoolProperty, FloatProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class PersonalSpaceInvader(HubsComponent):
    _definition = {
        'name': 'personal-space-invader',
        'display_name': 'Personal Space Invader',
        'category': Category.AVATAR,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MATSHADERBALL',
        'version': (1, 0, 0)
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
