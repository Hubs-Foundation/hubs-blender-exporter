import bpy
import mathutils
from bpy.types import (
    Gizmo
)


def hubs_gizmo_update(self, widget):
    widget.matrix_basis = self.matrix_world.normalized()
    bpy.context.view_layer.update()


def gizmo_update(self, widget):
    mat_scale = mathutils.Matrix.Scale(2.0, 4)
    widget.matrix_basis = self.matrix_world @ mat_scale
    bpy.context.view_layer.update()


class HubsGizmo(Gizmo):
    """Generic gizmo to render all Hubs gizmos"""
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
