import bpy
from bpy.props import StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Link(HubsComponent):
    _definition = {
        'name': 'link',
        'display_name': 'Link',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'LINKED',
        'deps': ['networked']
    }

    href: StringProperty(name="URL", description="URL",
                         default="https://mozilla.org")
