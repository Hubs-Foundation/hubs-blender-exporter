import bpy
from bpy.types import (Gizmo, GizmoGroup)
from .components_registry import get_components_registry
from mathutils import Matrix


def gizmo_update(obj, gizmo):
    loc, rot, _ = obj.matrix_world.decompose()
    mat_out = Matrix.LocRotScale(loc, rot, obj.dimensions)
    gizmo.matrix_basis = mat_out
    bpy.context.view_layer.update()


class HubsGizmo(Gizmo):
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
        if hasattr(self, "hba_gizmo_shape"):
            if not hasattr(self, "custom_shape"):
                self.draw_options = ()
                self.custom_shape = self.new_custom_shape(
                    'TRIS', self.hba_gizmo_shape)

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
        components_registry = get_components_registry()
        for obj in context.view_layer.objects:
            for component_item in obj.hubs_component_list.items:
                component_id = component_item.name
                component_class = components_registry[component_id]
                gizmo, update = component_class.create_gizmo(obj, self)
                if not component_id in self.widgets:
                    self.widgets[component_id] = {}
                self.widgets[component_id][obj] = (gizmo, update)

        self.refresh(context)

    def refresh(self, _):
        for component_id in self.widgets:
            for obj in self.widgets[component_id]:
                gizmo, update = self.widgets[component_id][obj]
                if gizmo:
                    self.refresh_object_gizmos(obj, gizmo, update)

    def refresh_object_gizmos(self, obj, gizmo, update):
        gizmo.hide = not obj.visible_get()
        update(obj, gizmo)


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
        wm = context.window_manager
        return wm.invoke_confirm(self, event)


class duplicate_override(bpy.types.Operator):
    """Override object duplicate operator to update gizmos after a duplicate"""
    bl_idname = "object.duplicate"
    bl_label = "Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

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

        for obj in copies:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

        update_gizmos()

        return {'FINISHED'}


def register_gizmo_classes():
    bpy.utils.register_class(HubsGizmo)
    bpy.utils.register_class(HubsGizmoGroup)


def unregister_gizmo_classes():
    bpy.utils.unregister_class(HubsGizmoGroup)
    bpy.utils.unregister_class(HubsGizmo)


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
        register_gizmo_classes()

    def unregister():
        bpy.utils.unregister_class(delete_override)
        bpy.utils.unregister_class(duplicate_override)
        unregister_gizmo_classes()

    return register, unregister


register, unregister = register_functions()
