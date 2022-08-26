import bpy
from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


def update(self, context):
    if context.object:
        context.object.hide_viewport = not context.object.hubs_component_visible.visible


class Visible(HubsComponent):
    _definition = {
        'name': 'visible',
        'display_name': 'Visible',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'HIDE_OFF'
    }

    visible: BoolProperty(name="Visible", default=True, update=update)
