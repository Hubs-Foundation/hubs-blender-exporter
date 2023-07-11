from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import has_component, add_component


class NavMesh(HubsComponent):
    _definition = {
        'name': 'nav-mesh',
        'display_name': 'Navigation Mesh',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'GRID',
        'version': (1, 0, 1),
        'deps': ['visible']
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

    @classmethod
    def init(cls, obj):
        obj.hubs_component_visible.visible = False
        obj.hubs_component_list.items.get('visible').isDependency = True

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 1):
            if not has_component(host, 'visible'):
                add_component(host, 'visible')
                host.hubs_component_visible.visible = False

            host.hubs_component_list.items.get('visible').isDependency = True
            migration_occurred = True

        return migration_occurred
