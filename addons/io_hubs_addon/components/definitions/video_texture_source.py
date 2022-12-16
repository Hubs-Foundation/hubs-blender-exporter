from ..utils import children_recursive
from bpy.props import IntVectorProperty, IntProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class VideoTextureSource(HubsComponent):
    _definition = {
        'name': 'video-texture-source',
        'display_name': 'Video Texture Source',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'VIEW_CAMERA',
        'version': (1, 0, 0)
    }

    resolution: IntVectorProperty(name="Resolution",
                                  description="Resolution",
                                  size=2,
                                  default=[1280, 720])

    fps: IntProperty(
        name="FPS", description="FPS", default=15)

    @classmethod
    def poll(cls, panel_type, host, ob=None):
        if panel_type == PanelType.OBJECT:
            return hasattr(
                host, 'type') and (
                host.type == 'CAMERA' or
                [x for x in children_recursive(host) if x.type == "CAMERA" and not x.parent_bone])
        elif panel_type == PanelType.BONE:
            return [x for x in children_recursive(ob) if x.type == "CAMERA" and x.parent_bone == host.name]
        return False

    @classmethod
    def get_unsupported_host_message(cls, panel_type, host):
        if panel_type == PanelType.BONE:
            host_reference = f"\"{host.name}\" in \"{host.id_data.name_full}\""
            object_message = ""
        else:
            host_reference = f"\"{host.name_full}\""
            object_message = " aren't cameras themselves and"

        host_type = panel_type.value
        message = f"Warning: Unsupported component on {host_type} {host_reference}, {host_type}s that{object_message} don't have a camera somewhere in their child hierarchy don't support {cls.get_display_name()} components"

        return message
