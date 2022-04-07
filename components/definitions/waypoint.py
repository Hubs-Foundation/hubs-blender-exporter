from bpy.props import BoolProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class hubs_component_waypoint(HubsComponent):
    _definition = {
        'export_name': 'waypoint',
        'display_name': 'Waypoint',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'pane_type': PanelType.OBJECT,
        'gizmo': 'waypoint',
        'icon': 'spawn-point.png'
    }

    canBeSpawnPoint: BoolProperty(
        name="canBeSpawnPoint",
        description="After each use, this waypoint will be disabled until the previous user moves away from it",
        default=False)

    canBeOccupied: BoolProperty(
        name="canBeOccupied",
        description="After each use, this waypoint will be disabled until the previous user moves away from it",
        default=False)

    canBeClicked: BoolProperty(
        name="canBeClicked",
        description="This waypoint will be visible in pause mode and clicking on it will teleport you to it",
        default=False)

    willDisableMotion: BoolProperty(
        name="willDisableMotion",
        description="Avatars will not be able to move while occupying his waypoint",
        default=False)

    willDisableTeleporting: BoolProperty(
        name="willDisableTeleporting",
        description="Avatars will not be able to teleport while occupying this waypoint",
        default=False)

    willMaintainInitialOrientation: BoolProperty(
        name="willMaintainInitialOrientation",
        description="Instead of rotating to face the same direction as the waypoint, avatars will maintain the orientation they started with before they teleported",
        default=False)

    snapToNavMesh: BoolProperty(
        name="snapToNavMesh",
        description="Avatars will move as close as they can to this waypoint but will not leave the ground",
        default=False)
