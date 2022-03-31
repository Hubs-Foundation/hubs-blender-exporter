import bpy
from bpy.types import (
    GizmoGroup,
)
from .gizmo_registry import registry
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
        for p in self.get_params(context):
            self.setup_param(context, p)

    def get_params(self, context):
        return [
            (obj, obj.hubs_gizmo_type)
            for obj in context.view_layer.objects
            if obj.type == 'EMPTY'
            and obj.visible_get()
            and hasattr(obj, "hubs_gizmo_type")
        ]

    def setup_param(self, context, param):
        ob, type = param
        if type not in registry:
            return
        info = registry[type]

        widget = self.gizmos.new(info.type)

        if (info.type == HubsGizmo.bl_idname):
            ## Ideally we should load the models from a glb but it throws an exception right now.
            # load_gizmo_model(info.id, info.path)
            # setattr(widget, "hba_gizmo_shape", load_gizmo_model(info.id, info.path))
            setattr(widget, "hba_gizmo_shape", info.shape)
            widget.setup()

        widget.draw_style = info.styles

        widget.matrix_basis = ob.matrix_world.normalized()
        widget.line_width = 3

        widget.color = info.color
        widget.alpha = 0.5
        widget.hide = False
        widget.hide_select = False

        widget.scale_basis = 1.0
        widget.use_draw_modal = True

        widget.color_highlight = info.color_highlight
        widget.alpha_highlight = 1.0

        op = widget.target_set_operator("transform.translate")
        op.constraint_axis = False, False, False
        op.orient_type = 'LOCAL'
        op.release_confirm = True

        self.widgets[ob.name] = widget
        self.refresh_param(context, param)

    def refresh(self, context):
        for p in self.get_params(context):
            self.refresh_param(context, p)

    def refresh_param(self, _, param):
        ob, type = param

        if ob.name not in self.widgets:
            return
        widget = self.widgets[ob.name]

        info = registry[type]
        info.update(ob, widget)


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
