from bpy.props import BoolProperty
from .hubs_component import HubsComponent
from ..types import PanelType, NodeType


class hubs_component_zone_audio_source(HubsComponent):
    _definition = {
        'export_name': 'zone-audio-source',
        'display_name': 'Zone Audio Source',
        'category': 'Elements',
        'node_type': NodeType.NODE,
        'pane_type': PanelType.OBJECT,
    }

    onlyMods: BoolProperty(
        name="Only Mods", description="Only room moderators should be able to transmit audio from this source.", default=True)

    muteSelf: BoolProperty(
        name="Mute Self", description="Do not transmit your own audio to audio targets.", default=True)

    debug: BoolProperty(
        name="Debug", description="Play white noise when no audio source is in the zone.", default=True)
