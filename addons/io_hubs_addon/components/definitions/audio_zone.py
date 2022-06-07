from bpy.props import BoolProperty
from ..gizmos import CustomModelGizmo
from ..models import box
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from mathutils import Matrix
from .networked import migrate_networked


def get_gizmo_scale(ob):
    if ob.type == 'MESH':
        return ob.dimensions.copy() / 2
    else:
        return ob.scale.copy() * ob.empty_display_size


class AudioZone(HubsComponent):
    _definition = {
        'name': 'audio-zone',
        'display_name': 'Audio Zone',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'deps': ['networked', 'audio-params'],
        'icon': 'MATCUBE'
    }

    inOut: BoolProperty(name="In Out",
                        description="The zone audio parameters affect the sources inside the zone when the listener is outside",
                        default=True)

    outIn: BoolProperty(name="Out In",
                        description="The zone audio parameters affect the sources outside the zone when the listener is inside",
                        default=True)

    @classmethod
    def update_gizmo(cls, ob, gizmo):
        loc, rot, _ = ob.matrix_world.decompose()
        scale = get_gizmo_scale(ob)
        mat_out = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        gizmo.matrix_basis = mat_out
        gizmo.hide = not ob.visible_get()

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        widget = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        widget.object = ob
        setattr(widget, "hubs_gizmo_shape", box.SHAPE)
        widget.setup()
        loc, rot, _ = ob.matrix_world.decompose()
        scale = get_gizmo_scale(ob)
        mat_out = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        widget.matrix_basis = mat_out
        widget.use_draw_scale = False
        widget.use_draw_modal = True
        widget.line_width = 3
        widget.color = (0.0, 0.8, 0.0)
        widget.alpha = 1.0
        widget.hide = not ob.visible_get()
        widget.hide_select = False
        widget.scale_basis = 1.0
        widget.color_highlight = (0.0, 0.8, 0.0)
        widget.alpha_highlight = 0.5

        op = widget.target_set_operator("transform.resize")
        op.constraint_axis = False, False, False
        op.orient_type = 'LOCAL'
        op.release_confirm = True

        return widget

    @classmethod
    def migrate(cls):
        migrate_networked(cls.get_name())
