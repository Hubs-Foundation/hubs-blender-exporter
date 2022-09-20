from ..hubs_component import HubsComponent
from bpy.props import StringProperty
from ..types import PanelType, NodeType
import uuid
from ..utils import add_component, has_component
import bpy
from bpy.app.handlers import persistent

DUPLICATE_OPS = (
    'OUTLINER_OT_id_paste',
    'OBJECT_OT_duplicate_move_linked',
    'OBJECT_OT_duplicate_move',
    'VIEW3D_OT_pastebuffer'
)

global operators_length


@persistent
def depsgraph_update(dummy):
    global operators_length
    wm = bpy.context.window_manager
    if wm.operators and len(wm.operators) != operators_length and wm.operators[-1].bl_idname in DUPLICATE_OPS:
        for ob in bpy.data.objects:
            if has_component(ob, Networked.get_name()):
                Networked.init(ob)
    operators_length = len(wm.operators)


class Networked(HubsComponent):
    _definition = {
        'name': 'networked',
        'display_name': 'Networked',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE]
    }

    id: StringProperty(
        name="Network ID",
        description="Network ID"
    )

    def draw(self, context, layout, panel):
        layout.label(text="Network ID:")
        layout.label(text=self.id)

    @classmethod
    def init(cls, obj):
        obj.hubs_component_networked.id = str(uuid.uuid4()).upper()

    @staticmethod
    def register():
        global operators_length
        operators_length = 0
        if not depsgraph_update in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)

    @staticmethod
    def unregister():
        if depsgraph_update in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)


def migrate_networked(component_name):
    def migrate_data(ob):
        if component_name in ob.hubs_component_list.items:
            if Networked.get_name() not in ob.hubs_component_list.items:
                add_component(ob, Networked.get_name())

        if has_component(ob, Networked.get_name()) and not ob.hubs_component_networked.id:
            Networked.init(ob)

    for ob in bpy.data.objects:
        migrate_data(ob)

        if ob.type == 'ARMATURE':
            for bone in ob.data.bones:
                migrate_data(bone)
