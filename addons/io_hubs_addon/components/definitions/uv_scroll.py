from bpy.props import FloatVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class UVScroll(HubsComponent):
    _definition = {
        'name': 'uv-scroll',
        'display_name': 'UV Scroll',
        'category': Category.ANIMATION,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'TEXTURE_DATA'
    }

    speed: FloatVectorProperty(name="Speed",
                               description="Speed",
                               size=2,
                               subtype="XYZ",
                               default=[0, 0])

    increment: FloatVectorProperty(name="Increment",
                                   description="Increment",
                                   size=2,
                                   subtype="XYZ",
                                   default=[0, 0])

    @classmethod
    def poll(cls, context, panel_type):
        return hasattr(context.object.data, 'materials')

    def draw(self, context, layout, panel):
        has_texture = False
        for material in context.object.data.materials:
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image != None:
                    has_texture = True

        super().draw(context, layout, panel)
        if not has_texture:
            layout.alert = True
            layout.label(text='This component requires an image texture',
                         icon='ERROR')
