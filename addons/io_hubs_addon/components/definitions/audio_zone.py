from bpy.props import BoolProperty
from ..gizmos import CustomModelGizmo
from ..models import box
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from mathutils import Matrix
from .networked import migrate_networked


class AudioZone(HubsComponent):
    _definition = {
        'name': 'audio-zone',
        'display_name': 'Audio Zone',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
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
    def update_gizmo(cls, ob, bone, target, gizmo):
        if bone:
            _, _, wScale = ob.matrix_world.decompose()
            loc, rot, _ = bone.matrix.to_4x4().decompose()
            scaleMat = Matrix.Diagonal(bone.bbone_scaleout).to_4x4(
            ) @ Matrix.Diagonal(wScale).to_4x4()
            mat_offset = Matrix.Translation(bone.tail - bone.head)
            mat = ob.matrix_world @ mat_offset @ Matrix.Translation(
                loc) @ rot.normalized().to_matrix().to_4x4() @ scaleMat
        else:
            loc, rot, scale = ob.matrix_world.decompose()
            scaleMat = Matrix.Diagonal(scale).to_4x4()
            mat = Matrix.Translation(
                loc) @ rot.normalized().to_matrix().to_4x4() @ scaleMat

        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        gizmo.object = ob
        setattr(gizmo, "hubs_gizmo_shape", box.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.line_width = 3
        gizmo.color = (0.0, 0.8, 0.0)
        gizmo.alpha = 1.0
        gizmo.hide_select = True
        gizmo.scale_basis = 1.0
        gizmo.color_highlight = (0.0, 0.8, 0.0)
        gizmo.alpha_highlight = 0.5

        return gizmo

    @classmethod
    def migrate(cls, version):
        migrate_networked(cls.get_name())
