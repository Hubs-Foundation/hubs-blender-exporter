from bpy.props import IntVectorProperty, IntProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class VideoTextureSource(HubsComponent):
    _definition = {
        'name': 'video-texture-source',
        'display_name': 'Video Texture Source',
        'category': Category.SCENE,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'VIEW_CAMERA'
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
        # TODO Should we listen to scene graph updates and remove the component if this is no longer satisfied to avoid dangling components?
        return context.object.type == 'CAMERA' or [x for x in context.object.children_recursive if x.type == "CAMERA"]
