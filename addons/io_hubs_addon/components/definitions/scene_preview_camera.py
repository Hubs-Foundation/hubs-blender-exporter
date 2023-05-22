from bpy.props import FloatVectorProperty, FloatProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class ScenePreviewCamera(HubsComponent):
    _definition = {
        'name': 'scene-preview-camera',
        'display_name': 'Scene Preview Camera',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
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
