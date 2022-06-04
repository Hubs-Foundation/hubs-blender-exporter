from math import radians
from ..models import spawn_point
from ..gizmos import CustomModelGizmo
from ..types import Category, PanelType, NodeType
from ..hubs_component import HubsComponent
from bpy.props import BoolProperty
from mathutils import Matrix
from .networked import migrate_networked


def get_gizmo_scale(ob):
    if ob.type == 'MESH':
        return ob.dimensions.copy() / 2
    else:
        return ob.scale.copy() * ob.empty_display_size


def get_gizmo_dimension(ob):
    if ob.type == 'MESH':
        return ob.dimensions.copy()
    else:
        return ob.scale.copy() * ob.empty_display_size * 2


class Waypoint(HubsComponent):
    _definition = {
        'name': 'waypoint',
        'display_name': 'Waypoint',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'gizmo': 'waypoint',
        'icon': 'spawn-point.png',
        'deps': ['networked']
    }

    canBeSpawnPoint: BoolProperty(
        name="canBeSpawnPoint",
        description="Avatars may be teleported to this waypoint when entering the scene",
        default=False)

    isOccupied: BoolProperty(
        name="isOccupied",
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

    willMaintainWorldUp: BoolProperty(
        name="willMaintainWorldUp",
        description="Instead of rotating to face the same direction as the waypoint, users will maintain the orientation they started with before they teleported",
        default=False)

    @classmethod
    def init(cls, ob):
        ob.hubs_component_media_frame.bounds = get_gizmo_dimension(ob)

    @classmethod
    def update_gizmo(cls, ob, gizmo):
        loc, rot, scale = ob.matrix_world.decompose()
        gizmo.matrix_basis = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        gizmo.hide = not ob.visible_get()

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        widget = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        widget.object = ob
        setattr(widget, "hubs_gizmo_shape", spawn_point.SHAPE)
        widget.setup()
        loc, rot, scale = ob.matrix_world.decompose()
        widget.matrix_basis = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        widget.use_draw_scale = False
        widget.use_draw_modal = True
        widget.color = (0.8, 0.8, 0.8)
        widget.alpha = 0.5
        widget.hide = not ob.visible_get()
        widget.scale_basis = 1.0
        widget.hide_select = False
        widget.color_highlight = (0.8, 0.8, 0.8)
        widget.alpha_highlight = 1.0

        op = widget.target_set_operator("transform.translate")
        op.constraint_axis = False, False, False
        op.orient_type = 'LOCAL'
        op.release_confirm = True

        return widget

    @classmethod
    def migrate(cls):
        migrate_networked(cls.get_name())
