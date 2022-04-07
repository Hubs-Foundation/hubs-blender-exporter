from bpy.props import IntVectorProperty, IntProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class hubs_component_video_texture_source(HubsComponent):
    _definition = {
        'id': 'video-texture-source',
        'display_name': 'Video Texture Source',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT_DATA
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
