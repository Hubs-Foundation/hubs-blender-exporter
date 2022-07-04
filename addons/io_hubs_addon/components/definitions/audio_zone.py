from bpy.props import BoolProperty, EnumProperty
from ..gizmos import CustomModelGizmo, bone_matrix_world, update_gizmos
from ..models import box, sphere
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


SHAPES = [("box", "Box", "Box Shape"),
          ("spehere", "Sphere", "Spehere shape")]


def update_shape(self, context):
    update_gizmos()
    return None


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

    shape: EnumProperty(name="Shape",
                        description="Shape of the Audio Zone",
                        items=SHAPES,
                        default="box",
                        update=update_shape
                        )

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
        shape = box.SHAPE if ob.hubs_component_audio_zone.shape == "box" else sphere.SHAPE
        setattr(gizmo, "hubs_gizmo_shape", shape)
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
