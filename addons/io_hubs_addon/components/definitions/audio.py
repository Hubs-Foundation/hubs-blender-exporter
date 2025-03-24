from ..models import audio
from ..gizmos import CustomModelGizmo, bone_matrix_world
from bpy.props import BoolProperty, StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


class Audio(HubsComponent):
    _definition = {
        'name': 'audio',
        'display_name': 'Audio',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked', 'audio-params'],
        'icon': 'OUTLINER_OB_SPEAKER',
        'version': (1, 0, 0),
        'tooltip': 'Load an audio file from a URL and play it.'
    }

    src: StringProperty(
        name="Audio URL", description="Audio URL", default='https://example.org/AudioFile.mp3')

    autoPlay: BoolProperty(name="Auto Play",
                           description="Auto Play",
                           default=True)

    controls: BoolProperty(
        name="Show controls",
        description="When enabled, shows play/pause, skip forward/back, and volume controls when hovering your cursor over it in Hubs",
        default=True)

    loop: BoolProperty(name="Loop",
                       description="Loop",
                       default=True)

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)

        return migration_occurred

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
        setattr(gizmo, "hubs_gizmo_shape", audio.SHAPE)
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
