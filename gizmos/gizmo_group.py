import bpy
from bpy.types import (
    GizmoGroup,
)
from .gizmo_registry import registry
from .types.hubs_gizmo import HubsGizmo


def load_gizmo_model(id, path):
    assert id != None, "No Gizmo id provided"
    assert path != None, "No Gizmo path provided"

    custom_shape_verts = []
    print("Gizmo model " + id + " load start: " + path)
    bpy.ops.import_scene.gltf(filepath=path)
    obj = bpy.data.objects[id]

    obj.data.calc_loop_triangles()
    for tri in obj.data.loop_triangles:
        for index in range(0, len(tri.vertices)):
            v = obj.data.vertices[tri.vertices[index]]
            co_final = obj.matrix_world @ v.co
            custom_shape_verts.append([co_final[0], co_final[1], co_final[2]])

    print(str(custom_shape_verts))
    bpy.data.objects.remove(obj, do_unlink=True)
    print("Gizmo model load end")

    return custom_shape_verts


class HubsGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_hba_gizmo_group"
    bl_label = "Object Camera Test Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL', 'SELECT'}

    def setup(self, context):
        self.widgets = {}
        for p in self.get_params(context):
            self.setup_param(context, p)

    def get_params(self, context):
        return [
            (obj, obj.HBA_component_type)
            for obj in context.view_layer.objects
            if obj.type == 'EMPTY'
            and obj.visible_get()
            and hasattr(obj, "HBA_component_type")
        ]

    def setup_param(self, context, param):
        ob, type = param
        if type not in registry:
            return
        info = registry[type]

        widget = self.gizmos.new(info.type)

        if (info.type == HubsGizmo.bl_idname):
            # Ideally we should load the models from a glb but for some reason it hangs
            # setattr(widget, "hba_gizmo_shape",
            #         utils.load_gizmo_model(info.id, info.path))
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
