from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class NavMesh(HubsComponent):
    _definition = {
        'name': 'nav-mesh',
        'display_name': 'Navigation Mesh',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'GRID',
        'version': (1, 0, 0)
    }

    @classmethod
    def poll(cls, panel_type, host, ob=None):
        return host.type == 'MESH'

    def draw(self, context, layout, panel):
        ob = context.object

        total = 0
        if ob.type == 'MESH' and ob.data and ob.data.materials:
            for material in ob.data.materials:
                if material:
                    total += 1

        if total > 1:
            col = layout.column()
            col.alert = True
            col.label(text='The Nav mesh should only have one material',
                      icon='ERROR')
