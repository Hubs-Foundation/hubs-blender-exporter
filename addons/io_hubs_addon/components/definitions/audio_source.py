from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class AudioSource(HubsComponent):
    _definition = {
        'name': 'zone-audio-source',
        'display_name': 'Audio Source',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MOD_WAVE',
        'version': (1, 0, 0)
    }

    onlyMods: BoolProperty(
        name="Only Mods", description="Only room moderators are able to transmit audio from this source", default=True)

    muteSelf: BoolProperty(
        name="Mute Self", description="Do not transmit your own audio to audio targets", default=True)

    debug: BoolProperty(
        name="Debug", description="Play white noise when no audio source is in the zone", default=False)
