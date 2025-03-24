from ..models import spawn_point
from ..gizmos import CustomModelGizmo, bone_matrix_world
from ..types import Category, PanelType, NodeType
from ..hubs_component import HubsComponent
from bpy.props import BoolProperty
from .networked import migrate_networked


class Waypoint(HubsComponent):
    _definition = {
        'name': 'waypoint',
        'display_name': 'Waypoint',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'gizmo': 'waypoint',
        'icon': 'spawn-point.png',
        'deps': ['networked'],
        'version': (1, 0, 0),
        'tooltip': "Add a waypoint to teleport to, can also be a spawn point"
    }

    canBeSpawnPoint: BoolProperty(
        name="Use As Spawn Point",
        description="Avatars may be teleported to this waypoint when entering the scene",
        default=False)

    canBeOccupied: BoolProperty(
        name="Can Be Occupied",
        description="After each use, this waypoint will be disabled until the previous user moves away from it",
        default=False)

    canBeClicked: BoolProperty(
        name="Clickable",
        description="This waypoint will be visible in pause mode and clicking on it will teleport you to it",
        default=False)

    willDisableMotion: BoolProperty(
        name="Disable Motion",
        description="Avatars will not be able to move while occupying this waypoint",
        default=False)

    willDisableTeleporting: BoolProperty(
        name="Disable Teleporting",
        description="Avatars will not be able to teleport while occupying this waypoint",
        default=False)

    willMaintainInitialOrientation: BoolProperty(
        name="Maintain Initial Orientation",
        description="Instead of rotating to face the same direction as the waypoint, avatars will maintain the orientation they started with before they teleported",
        default=False)

    snapToNavMesh: BoolProperty(
        name="Snap To NavMesh",
        description="Avatars will move as close as they can to this waypoint but will not leave the ground",
        default=False)

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        if bone:
            mat = bone_matrix_world(ob, bone)
        else:
            mat = ob.matrix_world.copy()

        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        gizmo.object = ob
        setattr(gizmo, "hubs_gizmo_shape", spawn_point.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.color = (0.8, 0.8, 0.8)
        gizmo.alpha = 0.5
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0

        return gizmo

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)

        return migration_occurred
