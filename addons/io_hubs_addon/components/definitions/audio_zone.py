from bpy.props import BoolProperty
from ..gizmos import CustomModelGizmo, bone_matrix_world
from ..models import box
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


class AudioZone(HubsComponent):
    _definition = {
        'name': 'audio-zone',
        'display_name': 'Audio Zone',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked', 'audio-params'],
        'icon': 'MATCUBE',
        'version': (1, 0, 0),
        'tooltip': 'Define an audio zone to control audio parameters within a specific area'
    }

    inOut: BoolProperty(
        name="In Out",
        description="The zone audio parameters affect the sources inside the zone when the listener is outside",
        default=True)

    outIn: BoolProperty(
        name="Out In",
        description="The zone audio parameters affect the sources outside the zone when the listener is inside",
        default=True)

    dynamic: BoolProperty(
        name="Dynamic",
        description="Whether or not this audio-zone will be movable",
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
    def init(cls, obj):
        obj.hubs_component_audio_params.overrideAudioSettings = True

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)

        return migration_occurred
