from bpy.props import BoolProperty, PointerProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import has_components
from bpy.types import Object

required_components = ['hubs_component_video_texture_source']


def filter_on_component(self, o):
    return has_components(o, required_components)


class hubs_component_video_texture_target(HubsComponent):
    _definition = {
        'export_name': 'video-texture-target',
        'display_name': 'Video Texture Target',
        'category': Category.AVATAR,
        'node_type': NodeType.MATERIAL,
        'panel_type': PanelType.MATERIAL
    }

    targetBaseColorMap: BoolProperty(
        name="Override Base Color Map", description="Should the video texture override the base color map?", default=True)

    targetEmissiveMap: BoolProperty(
        name="Override Emissive Color Map", description="Should the video texture override the emissive map?", default=True)

    srcNode: PointerProperty(
        name="Source",
        description="Node with a vide-texture-source to pull video from",
        type=Object,
        poll=filter_on_component)

    @classmethod
    def poll(cls, context):
        return len(context.object.material_slots) > 0


0
