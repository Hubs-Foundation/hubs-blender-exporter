import bpy
from bpy.props import BoolProperty, PointerProperty
from bpy.types import PropertyGroup


def update_visible(self, context):
    bpy.ops.object.hba_component_visible_switch()


class VisibleComponentProperties(PropertyGroup):
    visible: BoolProperty(name="Visible", default=True, update=update_visible)


class HBAComponentVisibleSwitch(bpy.types.Operator):
    bl_idname = "object.hba_component_visible_switch"
    bl_label = "Change Visible component state"
    bl_options = {"UNDO"}

    def execute(self, context):
        context.object.hide_viewport = not bpy.context.object.HBA_object_component_visible.visible
        return {"FINISHED"}


class HBAComponentVisibleAdd(bpy.types.Operator):
    bl_idname = "object.hba_component_visible_add"
    bl_label = "Add Visible component"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        bpy.context.object.HBA_object_component_visible.visible = True
        context.object.hide_viewport = not bpy.context.object.HBA_object_component_visible.visible
        return {"FINISHED"}


class RENDER_PT_hba_component_visible(bpy.types.Panel):
    bl_idname = "HBA_PT_Component_Visible"
    bl_label = "Visible"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        # TODO Add check to see if the component Visible has been added
        return context.object.type == 'MESH'

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj.HBA_object_component_visible,
                 "visible", text="Visible")
        row = layout.row()


def register():
    bpy.utils.register_class(VisibleComponentProperties)
    bpy.types.Object.HBA_object_component_visible = PointerProperty(
        type=VisibleComponentProperties)
    bpy.utils.register_class(HBAComponentVisibleSwitch)
    bpy.utils.register_class(HBAComponentVisibleAdd)
    bpy.utils.register_class(RENDER_PT_hba_component_visible)


def unregister():
    bpy.utils.unregister_class(RENDER_PT_hba_component_visible)
    bpy.utils.unregister_class(HBAComponentVisibleAdd)
    bpy.utils.unregister_class(HBAComponentVisibleSwitch)
    del bpy.types.Object.HBA_object_component_visible
    bpy.utils.unregister_class(VisibleComponentProperties)
