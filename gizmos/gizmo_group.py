import bpy
from bpy.types import (
    GizmoGroup,
)
from .gizmo_registry import get_components_registry
from .gizmo_custom import HubsGizmo
from .utils import load_gizmo_model


class HubsGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_hba_gizmo_group"
    bl_label = "Hubs gizmo group"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL', 'SELECT'}

    def setup(self, context):
        self.widgets = {}
        self.widgets_types = {}
        for obj in self.get_objects_with_gizmos(context):
            self.widgets[obj.name] = []
            self.setup_gizmos(context, obj)

    def get_objects_with_gizmos(self, context):
        return [
            obj
            for _, obj in bpy.context.scene.objects.items()
            if hasattr(obj, "hubs_object_gizmos")
        ]

    def setup_gizmos(self, context, obj):
        gizmos_registry = get_components_registry()
        for gizmo in obj.hubs_object_gizmos:
            if gizmo.name not in gizmos_registry:
                return
            info = gizmos_registry[gizmo.name]

            widget = self.gizmos.new(info.type)

            if (info.type == HubsGizmo.bl_idname):
                # Ideally we should load the models from a glb but it throws an exception right now.
                # load_gizmo_model(info.id, info.path)
                # setattr(widget, "hba_gizmo_shape", load_gizmo_model(info.id, info.path))
                setattr(widget, "hba_gizmo_shape", info.shape)
                widget.setup()

            widget.draw_style = info.styles

            widget.matrix_basis = obj.matrix_world.normalized()
            widget.line_width = 3

            widget.color = info.color
            widget.alpha = 0.5
            widget.hide = not obj.visible_get()
            widget.hide_select = True

            widget.scale_basis = 1.0
            widget.use_draw_modal = True

            widget.color_highlight = info.color_highlight
            widget.alpha_highlight = 1.0

            op = widget.target_set_operator("transform.translate")
            op.constraint_axis = False, False, False
            op.orient_type = 'LOCAL'
            op.release_confirm = True

            self.widgets[obj.name].append(widget)
            self.widgets_types[id(widget)] = gizmo.name
            self.refresh_gizmos(context, obj)

    def refresh(self, context):
        for obj in self.get_objects_with_gizmos(context):
            self.refresh_gizmos(context, obj)

    def refresh_gizmos(self, _, obj):
        if obj.name not in self.widgets:
            return

        gizmos_registry = get_components_registry()

        widgets = self.widgets[obj.name]
        for widget in widgets:
            if id(widget) not in self.widgets_types:
                return

            widget.hide = not obj.visible_get()

            info = gizmos_registry[self.widgets_types[id(widget)]]
            info.update(obj, widget)


classes = (
    HubsGizmo,
    HubsGizmoGroup
)

register, unregister = bpy.utils.register_classes_factory(classes)


def update_gizmos(self, context):
    try:
        unregister()
    except:
        pass
    register()
