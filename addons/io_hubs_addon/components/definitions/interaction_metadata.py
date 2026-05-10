from bpy.props import StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class InteractionMetadata(HubsComponent):
    _definition = {
        'name': 'interaction-metadata',
        'display_name': 'Interaction Metadata',
        'category': Category.MISC,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'PROPERTIES',
        'version': (1, 0, 0)
    }

    behavior_type: StringProperty(
        name="Behavior Type",
        description="High-level behavior classification for downstream systems",
        default=""
    )

    interaction_profile: StringProperty(
        name="Interaction Profile",
        description="Interaction mode or profile name",
        default=""
    )

    simulation_tag: StringProperty(
        name="Simulation Tag",
        description="Simulation or systems tag for exported content",
        default=""
    )

    def gather(self, export_settings, object):
        data = {}

        if self.behavior_type.strip():
            data["behaviorType"] = self.behavior_type.strip()

        if self.interaction_profile.strip():
            data["interactionProfile"] = self.interaction_profile.strip()

        if self.simulation_tag.strip():
            data["simulationTag"] = self.simulation_tag.strip()

        return data
