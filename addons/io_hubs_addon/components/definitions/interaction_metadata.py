from bpy.props import EnumProperty, StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


BEHAVIOR_TYPE_ITEMS = [
    ("", "None", "No behavior type"),
    ("agent", "Agent", "Autonomous agent"),
    ("swarm", "Swarm", "Swarm / multi-agent system"),
    ("trigger", "Trigger", "Trigger-based interaction"),
    ("sensor", "Sensor", "Sensor or detection entity"),
    ("static", "Static", "Non-interactive object"),
]


INTERACTION_PROFILE_ITEMS = [
    ("", "None", "No interaction profile"),
    ("grabbable", "Grabbable", "User can grab"),
    ("clickable", "Clickable", "User can click"),
    ("hoverable", "Hoverable", "Responds to hover"),
    ("physics", "Physics", "Physics-driven interaction"),
    ("ui", "UI", "User interface element"),
]


class InteractionMetadata(HubsComponent):
    _definition = {
        'name': 'interaction-metadata',
        'display_name': 'Interaction Metadata',
        'category': Category.MISC,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'PROPERTIES',
        'version': (1, 1, 0)  # bump version
    }

    behavior_type: EnumProperty(
        name="Behavior Type",
        description="High-level behavior classification",
        items=BEHAVIOR_TYPE_ITEMS,
        default=""
    )

    interaction_profile: EnumProperty(
        name="Interaction Profile",
        description="Interaction mode",
        items=INTERACTION_PROFILE_ITEMS,
        default=""
    )

    simulation_tag: StringProperty(
        name="Simulation Tag",
        description="Custom simulation tag",
        default=""
    )

    def gather(self, export_settings, object):
        data = {}

        if self.behavior_type:
            data["behaviorType"] = self.behavior_type

        if self.interaction_profile:
            data["interactionProfile"] = self.interaction_profile

        if self.simulation_tag.strip():
            data["simulationTag"] = self.simulation_tag.strip()

        return data
