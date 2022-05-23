import bpy
from bpy.props import BoolProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


def update(self, context):
    context.object.hide_viewport = not bpy.context.object.hubs_component_visible.visible


class Visible(HubsComponent):
    _definition = {
        'name': 'visible',
        'display_name': 'Visible',
        'category': Category.OBJECT,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'HIDE_OFF'
    }

    visible: BoolProperty(name="Visible", default=True, update=update)
