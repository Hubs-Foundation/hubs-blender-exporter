from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..gizmos import CustomModelGizmo
from ..models import scene_preview_camera
from mathutils import Matrix
from math import radians


class ScenePreviewCamera(HubsComponent):
    _definition = {
        'name': 'scene-preview-camera',
        'display_name': 'Scene Preview Camera',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'CAMERA_DATA',
        'version': (1, 0, 0)
    }

    def pre_export(self, export_settings, host, ob=None):
        global backup_name
        backup_name = host.name
        host.name = 'scene-preview-camera'

    def post_export(self, export_settings, host, ob=None):
        global backup_name
        host.name = backup_name
        backup_name = ""

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        mat = ob.matrix_world.copy()
        
        rot_offset = Matrix.Rotation(radians(180), 4, 'Z')
        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat @ rot_offset

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        gizmo.object = ob
        setattr(gizmo, "hubs_gizmo_shape", scene_preview_camera.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.alpha = 0.5
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0

        return gizmo