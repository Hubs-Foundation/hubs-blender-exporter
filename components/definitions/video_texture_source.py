from bpy.props import IntVectorProperty, IntProperty
from .hubs_component import HubsComponent
from ..types import PanelType, NodeType


class hubs_component_video_texture_source(HubsComponent):
    _definition = {
        'export_name': 'video-texture-source',
        'display_name': 'Video Texture Source',
        'category': 'Scene',
        'node_type': NodeType.NODE,
        'pane_type': PanelType.OBJECT_DATA
    }

    resolution: IntVectorProperty(name="Resolution",
                                  description="Resolution",
                                  size=2,
                                  subtype='COORDINATES',
                                  default=[1280, 720])

    fps: IntProperty(
        name="FPS", description="FPS", default=15)

    @classmethod
    def poll(cls, context):
        return context.object.type == 'CAMERA'
