from bpy.props import StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Pdf(HubsComponent):
    _definition = {
        'name': 'pdf',
        'display_name': 'Pdf',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked'],
        'icon': 'FILE_IMAGE',
        'version': (1, 0, 0)
    }

    src: StringProperty(
        name="Pdf URL", description="The web address of the pdf", default='https://mozilla.org')
