from ..utils import children_recursive
from bpy.props import IntVectorProperty, IntProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class VideoTextureSource(HubsComponent):
    _definition = {
        'name': 'video-texture-source',
        'display_name': 'Video Texture Source',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'VIEW_CAMERA'
    }

    resolution: IntVectorProperty(name="Resolution",
                                  description="Resolution",
                                  size=2,
                                  default=[1280, 720])

    fps: IntProperty(
        name="FPS", description="FPS", default=15)

    def draw(self, context, layout):
        if context.object.type == 'CAMERA' or [x for x in children_recursive(context.object) if x.type == "CAMERA"]:
            super().draw(context, layout)
        else:
            col = layout.column()
            col.alert = True
            col.label(text='No camera found in the object hierarchy',
                      icon='ERROR')
