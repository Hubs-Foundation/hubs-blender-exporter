import bpy
from bpy.props import BoolProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


def update(self, context):
    context.object.hide_viewport = not bpy.context.object.hubs_component_visible.visible


class Visible(HubsComponent):
    _definition = {
        'id': 'visible',
        'name': 'hubs_component_visible',
        'display_name': 'Visible',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'eye.png'
    }

    visible: BoolProperty(name="Visible", default=True, update=update)