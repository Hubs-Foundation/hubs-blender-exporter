import atexit
import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty
from bpy.types import PropertyGroup, Menu, Operator
from bpy.types import PropertyGroup
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class ActionsList(bpy.types.UIList):
    bl_idname = "HUBS_UL_ACTIONS_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        key_block = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.90, align=False)
            split.prop(key_block, "name", text="",
                       emboss=False, icon_value=icon)
            row = split.row(align=True)
            row.emboss = 'NONE_OR_STATUS'
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class AddActionOperator(Operator):
    bl_idname = "hubs_loop_animation.add_action"
    bl_label = "Add Action"

    action_name: StringProperty(
        name="Action Name", description="Action Name", default="")

    def execute(self, context):
        ob = context.object
        action = ob.hubs_component_loop_animation.actions_list.add()
        action.name = self.action_name

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class RemoveActionOperator(Operator):
    bl_idname = "hubs_loop_animation.remove_action"
    bl_label = "Remove Action"

    @classmethod
    def poll(self, context):
        return context.object.hubs_component_loop_animation.active_action_key != -1

    def execute(self, context):
        ob = context.object

        active_action_key = ob.hubs_component_loop_animation.active_action_key
        ob.hubs_component_loop_animation.actions_list.remove(
            active_action_key)

        return {'FINISHED'}


def has_action(actions_list, action):
    exists = False
    for item in actions_list:
        if item.name == action:
            exists = True
            break

    return exists


class ActionsContextMenu(Menu):
    bl_idname = "HUBS_MT_ACTIONS_context_menu"
    bl_label = "Actions Specials"

    def draw(self, context):
        no_actions = True
        for a in bpy.data.actions:
            if not has_action(context.object.hubs_component_loop_animation.actions_list, a.name):
                self.layout.operator(AddActionOperator.bl_idname, icon='OBJECT_DATA',
                                     text=a.name).action_name = a.name
                no_actions = False

        if no_actions:
            self.layout.label(text="No actions found")


class ActionPropertyType(PropertyGroup):
    name: StringProperty(
        name="Action name",
        description="Action Name",
        default=""
    )


bpy.utils.register_class(ActionPropertyType)


@atexit.register
def unregister():
    bpy.utils.unregister_class(ActionPropertyType)


class LoopAnimation(HubsComponent):
    _definition = {
        'id': 'loop-animation',
        'name': 'hubs_component_loop_animation',
        'display_name': 'Loop Animation',
        'category': Category.ANIMATION,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'LOOP_BACK'
    }

    actions_list: CollectionProperty(
        type=ActionPropertyType)

    clip: StringProperty(
        name="Animation Clip",
        description="Animation clip to use",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    active_action_key: IntProperty(
        name="Active action index",
        description="Active action index",
        default=-1
    )

    paused: BoolProperty(
        name="Paused",
        description="Paused",
        default=False
    )

    def draw(self, context, layout):
        layout.label(text='Animations to play:')

        row = layout.row()
        row.template_list(ActionsList.bl_idname, "", self,
                          "actions_list", self, "active_action_key", rows=3)

        col = row.column(align=True)

        col.menu(ActionsContextMenu.bl_idname, icon='ADD', text="")
        col.operator(RemoveActionOperator.bl_idname,
                     icon='REMOVE', text="")

        layout.separator()

        layout.prop(data=self, property='paused')

    def gather(self, export_settings, object):
        return {
            'clip': ",".join(
                object.hubs_component_loop_animation.actions_list.keys()),
            'paused': self.paused
        }

    @staticmethod
    def register():
        bpy.utils.register_class(ActionsList)
        bpy.utils.register_class(ActionsContextMenu)
        bpy.utils.register_class(AddActionOperator)
        bpy.utils.register_class(RemoveActionOperator)

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(ActionsList)
        bpy.utils.unregister_class(ActionsContextMenu)
        bpy.utils.unregister_class(AddActionOperator)
        bpy.utils.unregister_class(RemoveActionOperator)

    @classmethod
    def migrate(cls):
        for ob in bpy.data.objects:
            if cls.get_id() in ob.hubs_component_list.items:
                actions = ob.hubs_component_loop_animation.clip.split(",")
                for action_name in actions:
                    if not has_action(ob.hubs_component_loop_animation.actions_list, action_name):
                        action = ob.hubs_component_loop_animation.actions_list.add()
                        action.name = action_name.strip()
