import bpy
from bpy.types import (Gizmo, GizmoGroup)
from bpy.props import BoolProperty
from .components_registry import get_component_by_name
from bpy.app.handlers import persistent
from mathutils import Vector


def gizmo_update(obj, gizmo):
    gizmo.matrix_basis = obj.matrix_world.normalized()


def process_input_axis(event, out_value, delta, axis_state):
    if event.value == 'PRESS':
        if event.type in ['X', 'Y', 'Z']:
            axis = event.type.lower()
            if not event.shift:
                axis_state.xyz = (
                    not getattr(axis_state, 'x') if axis == 'x' else False,
                    not getattr(axis_state, 'y') if axis == 'y' else False,
                    not getattr(axis_state, 'z') if axis == 'z' else False)
            else:
                axis_state.xyz = (False if axis == 'x' else not axis_state.x,
                                  False if axis == 'y' else not axis_state.y,
                                  False if axis == 'z' else not axis_state.z)

    if not axis_state.x and not axis_state.y and not axis_state.z:
        out_value += Vector((delta, delta, delta))
    else:
        if axis_state.x:
            out_value.x += delta
        if axis_state.y:
            out_value.y += delta
        if axis_state.z:
            out_value.z += delta


class CustomModelGizmo(Gizmo):
    """Generic gizmo to render all Hubs custom gizmos"""
    bl_idname = "GIZMO_GT_hba_gizmo"

    __slots__ = (
        "object",
        "hubs_gizmo_shape",
        "custom_shape",
    )

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def setup(self):
        if hasattr(self, "hubs_gizmo_shape"):
            self.custom_shape = self.new_custom_shape(
                'TRIS', self.hubs_gizmo_shape)

    def invoke(self, context, event):
        if hasattr(self, "object"):
            if not event.shift:
                bpy.ops.object.select_all(action='DESELECT')
            self.object.select_set(True)
            bpy.context.view_layer.objects.active = self.object
        return {'RUNNING_MODAL'}

    def modal(self, context, event, tweak):
        return {'RUNNING_MODAL'}


class HubsGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_hba_gizmo_group"
    bl_label = "Hubs gizmo group"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL', 'SELECT'}

    def setup(self, context):
        self.widgets = {}
        for ob in context.view_layer.objects:
            for component_item in ob.hubs_component_list.items:
                component_name = component_item.name
                component_class = get_component_by_name(component_name)
                if not component_class:
                    continue
                gizmo = component_class.create_gizmo(ob, self)
                if gizmo:
                    if not component_name in self.widgets:
                        self.widgets[component_name] = {}
                    self.widgets[component_name][ob.name] = gizmo

        self.refresh(context)

    def refresh(self, context):
        for component_name in self.widgets:
            components_widgets = self.widgets[component_name].copy()
            for ob_name in components_widgets:
                gizmo = components_widgets[ob_name]
                if gizmo and gizmo in self.gizmos.values():
                    if ob_name in bpy.data.objects:
                        component_class = get_component_by_name(component_name)
                        component_class.update_gizmo(
                            bpy.data.objects[ob_name], gizmo)
                    else:
                        self.gizmos.remove(gizmo)
                        del self.widgets[component_name][ob_name]


class delete_override(bpy.types.Operator):
    """Override object delete operator to update gizmos after deletion"""
    bl_idname = "object.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}

    use_global: bpy.props.BoolProperty(default=True)
    confirm: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for obj in context.selected_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        update_gizmos()

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class duplicate_override(bpy.types.Operator):
    """Override object duplicate operator to update gizmos after a duplicate"""
    bl_idname = "object.duplicate"
    bl_label = "Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    linked: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        copies = []
        for obj in context.selected_objects:
            copy = obj.copy()
            curr_collection = context.view_layer.active_layer_collection.name
            bpy.data.collections[curr_collection].objects.link(copy)
            copies.append(copy)
            obj.select_set(False)
            if obj.data and not self.linked:
                copy.data = obj.data.copy()
                if obj.animation_data:
                    copy.animation_data.action = obj.animation_data.action.copy()

        for obj in copies:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

        update_gizmos()

        return {'FINISHED'}


@persistent
def undo_post(dummy):
    update_gizmos()


@persistent
def redo_post(dummy):
    update_gizmos()


def register_gizmo_classes():
    bpy.utils.register_class(CustomModelGizmo)
    bpy.utils.register_class(HubsGizmoGroup)


def unregister_gizmo_classes():
    bpy.utils.unregister_class(HubsGizmoGroup)
    bpy.utils.unregister_class(CustomModelGizmo)


def update_gizmos():
    try:
        unregister_gizmo_classes()
    except:
        pass

    register_gizmo_classes()


def register_functions():
    def register():
        bpy.utils.register_class(delete_override)
        bpy.utils.register_class(duplicate_override)
        if not undo_post in bpy.app.handlers.undo_post:
            bpy.app.handlers.undo_post.append(undo_post)
        if not redo_post in bpy.app.handlers.redo_post:
            bpy.app.handlers.redo_post.append(redo_post)
        register_gizmo_classes()

    def unregister():
        bpy.utils.unregister_class(delete_override)
        bpy.utils.unregister_class(duplicate_override)
        if not undo_post in bpy.app.handlers.undo_post:
            bpy.app.handlers.undo_post.remove(undo_post)
        if not redo_post in bpy.app.handlers.redo_post:
            bpy.app.handlers.redo_post.remove(redo_post)
        unregister_gizmo_classes()

    return register, unregister


register, unregister = register_functions()
