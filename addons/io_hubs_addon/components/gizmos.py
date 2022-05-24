import bpy
from bpy.types import (Gizmo, GizmoGroup)
from bpy.props import BoolProperty
from .components_registry import get_component_by_name
from mathutils import Matrix
from bpy.app.handlers import persistent


def gizmo_update(obj, gizmo):
    loc, rot, _ = obj.matrix_world.decompose()
    mat_out = Matrix.LocRotScale(loc, rot, obj.dimensions)
    gizmo.matrix_basis = mat_out


class CustomModelGizmo(Gizmo):
    """Generic gizmo to render all Hubs custom gizmos"""
    bl_idname = "GIZMO_GT_hba_gizmo"
    bl_target_properties = (
        {"id": "location", "type": 'FLOAT', "array_length": 3},
    )

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def setup(self):
        if hasattr(self, "hubs_gizmo_shape"):
            self.draw_options = ()
            self.custom_shape = self.new_custom_shape(
                'TRIS', self.hubs_gizmo_shape)

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
                if not component_name in self.widgets:
                    self.widgets[component_name] = {}
                self.widgets[component_name][ob] = gizmo

        self.refresh(context)

    def refresh(self, context):
        for component_name in self.widgets:
            for ob in self.widgets[component_name]:
                gizmo = self.widgets[component_name][ob]
                if gizmo:
                    component_class = get_component_by_name(component_name)
                    component_class.update_gizmo(ob, gizmo)


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
            if not self.linked:
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
