from bpy.props import FloatProperty, BoolProperty, PointerProperty
from .hubs_component import HubsComponent
from ..utils import has_components
from ..types import Category, PanelType, NodeType
from bpy.types import Object

required_components = ['hubs_component_zone_audio_source']


def filter_on_component(self, o):
    return has_components(o, required_components)


class AudioTarget(HubsComponent):
    _definition = {
        'id': 'audio-target',
        'name': 'hubs_component_audio_target',
        'display_name': 'Audio Target',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'deps': ['audio-params'],
        'icon': 'SPEAKER'
    }

    srcNode: PointerProperty(
        name="Source",
        description="Node with a audio-source-zone to pull audio from",
        type=Object,
        poll=filter_on_component)

    minDelay: FloatProperty(
        name="Min Delay", description="Minimum random delay applied to the source audio", default=0.01, min=0.0, soft_min=0.0)

    maxDelay: FloatProperty(
        name="Max Delay", description="Maximum random delay applied to the source audio", default=0.03, min=0.0, soft_min=0.0)

    debug: BoolProperty(
        name="Debug", description="Show debug visuals", default=False)
