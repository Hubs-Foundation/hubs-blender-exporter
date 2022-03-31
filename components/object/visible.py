import bpy
from bpy.props import BoolProperty, PointerProperty
from bpy.types import PropertyGroup
from ..utils import *


COMPONENT_NAME = 'visible'

def update(self, context):
    context.object.hide_viewport = not bpy.context.object.hubs_component_visible.visible

class VisibleComponentProperties(PropertyGroup):
    visible: BoolProperty(name="Visible", default=True, update=update)

class HBAComponentVisibleAdd(bpy.types.Operator):
    bl_idname = "object.hba_component_visible_add"
    bl_label = "Add Visible component"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        add_component(bpy.context.object, COMPONENT_NAME)

        bpy.context.object.hubs_component_visible.visible = True
        context.object.hide_viewport = not bpy.context.object.hubs_component_visible.visible
        return {"FINISHED"}

class HBAComponentVisibleRemove(bpy.types.Operator):
    bl_idname = "object.hba_component_visible_remove"
    bl_label = "Remove Visible component"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        remove_component(bpy.context.object, COMPONENT_NAME)

        context.object.hide_viewport = False
        return {"FINISHED"}

class HBAComponentVisiblePanel(bpy.types.Panel):
    bl_idname = "HBA_PT_Component_Visible"
    bl_label = "Visible"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return has_component(context.object, COMPONENT_NAME)

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj.hubs_component_visible,
                 "visible", text="Visible")
        row = layout.row()


def register():
    bpy.utils.register_class(VisibleComponentProperties)
    bpy.types.Object.hubs_component_visible = PointerProperty(
        type=VisibleComponentProperties)
    bpy.utils.register_class(HBAComponentVisibleAdd)
    bpy.utils.register_class(HBAComponentVisiblePanel)


def unregister():
    bpy.utils.unregister_class(HBAComponentVisiblePanel)
    bpy.utils.unregister_class(HBAComponentVisibleAdd)
    del bpy.types.Object.hubs_component_visible
    bpy.utils.unregister_class(VisibleComponentProperties)
