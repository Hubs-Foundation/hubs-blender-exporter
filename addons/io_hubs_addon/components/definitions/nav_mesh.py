from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class NavMesh(HubsComponent):
    _definition = {
        'id': 'nav-mesh',
        'name': 'hubs_component_nav_mesh',
        'display_name': 'Navigation Mesh',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'GRID'
    }

    @classmethod
    def poll(cls, context):
        return context.object.type == 'MESH'
