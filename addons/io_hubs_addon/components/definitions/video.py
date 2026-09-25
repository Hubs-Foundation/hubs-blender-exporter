from ..models import video
from ..gizmos import CustomModelGizmo, bone_matrix_world
from bpy.props import BoolProperty, EnumProperty, StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..consts import PROJECTION_MODE
from .networked import migrate_networked
from ...io.utils import import_component, assign_property


class Video(HubsComponent):
    _definition = {
        'name': 'video',
        'display_name': 'Video',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked', 'audio-params'],
        'icon': 'FILE_MOVIE',
        'version': (1, 0, 0)
    }

    src: StringProperty(
        name="Video URL", description="The web address of the video", default='https://example.org/VideoFile.webm')

    projection: EnumProperty(
        name="Projection",
        description="Projection",
        items=PROJECTION_MODE,
        default="flat")

    autoPlay: BoolProperty(name="Auto Play",
                           description="Auto Play",
                           default=True)

    controls: BoolProperty(
        name="Show controls",
        description="When enabled, shows play/pause, skip forward/back, and, if the video contains audio, volume controls when hovering your cursor over it in Hubs",
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
    def gather_import(cls, gltf, blender_host, component_name, component_value, import_report, blender_ob=None):
        component = import_component(component_name, blender_host)
        audio_params_component = blender_host.hubs_component_audio_params
        if component_value:
            for property_name, property_value in component_value.items():
                if property_name in component.get_properties():
                    assign_property(gltf.vnodes,
                                    blender_host, component,
                                    property_name, property_value,
                                    import_report, blender_ob=blender_ob)
                else:
                    # Some video components have included audio-params properties directly, so if it's not a video component property, try assigning it to the audio-params component.
                    if property_name == "volume":
                        property_name = "gain"
                    audio_params_component.overrideAudioSettings = True
                    assign_property(gltf.vnodes,
                                    blender_host, audio_params_component,
                                    property_name, property_value,
                                    import_report, blender_ob=blender_ob)

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
        setattr(gizmo, "hubs_gizmo_shape", video.SHAPE)
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
