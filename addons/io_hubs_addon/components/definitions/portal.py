import bpy
from bpy.props import FloatVectorProperty
from ..gizmos import bone_matrix_world, CustomModelGizmo
from ..models import portal, box
from ..types import Category, PanelType, NodeType
from ..hubs_component import HubsComponent
from mathutils import Matrix, Vector
from bpy.types import (Gizmo)


class PortalBoundsGizmo(Gizmo):
    """Portal gizmo"""
    bl_idname = "GIZMO_GT_hba_portal_gizmo"
    bl_target_properties = (
        {"id": "bounds", "type": 'FLOAT', "array_length": 3},
        {"id": "offset", "type": 'FLOAT', "array_length": 3},
    )

    __slots__ = (
        "hubs_gizmo_shape",
        "custom_shape",
    )

    def _update_offset_matrix(self):
        loc, rot, _ = self.matrix_basis.decompose()
        scale = self.target_get_value("bounds")
        offset = self.target_get_value("offset")
        mat_out = Matrix.Translation(loc) @ rot.normalized().to_matrix().to_4x4()
        mat_off = Matrix.Translation(offset) @ Matrix.Diagonal(scale).to_4x4()
        self.matrix_basis = mat_out
        self.matrix_offset = mat_off

    def draw(self, context):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def setup(self):
        if hasattr(self, "hubs_gizmo_shape"):
            self.custom_shape = self.new_custom_shape(
                'TRIS', self.hubs_gizmo_shape)


class Portal(HubsComponent):
    _definition = {
        'name': 'portal',
        'display_name': 'Portal',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE]
    }

    bounds: FloatVectorProperty(
        name="Bounds",
        description="Trigger area bounds",
        unit='LENGTH',
        subtype="XYZ",
        default=(1.0, 1.0, 2.0))

    offset: FloatVectorProperty(
        name="Offset",
        description="Trigger area offset",
        unit='NONE',
        subtype="COORDINATES",
        default=(0.0, 0.5, 0.0))

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        if isinstance(gizmo, PortalBoundsGizmo):
            gizmo.target_set_prop(
                "bounds", target.hubs_component_portal, "bounds")
            gizmo.target_set_prop(
                "offset", target.hubs_component_portal, "offset")

            scale = gizmo.target_get_value("bounds")
            offset = gizmo.target_get_value("offset")
            mat_off = Matrix.Translation(offset) @ Matrix.Diagonal(scale).to_4x4()
            if bone:
                mat = bone_matrix_world(ob, bone, scale)
            else:
                loc, rot, _ = ob.matrix_world.decompose()
                mat = Matrix.Translation(loc) @ rot.normalized().to_matrix().to_4x4()

            gizmo.matrix_basis = mat
            gizmo.matrix_offset = mat_off
        else:
            loc, rot, _ = ob.matrix_world.decompose()
            mat = Matrix.Translation(loc) @ rot.normalized().to_matrix().to_4x4()
            gizmo.matrix_basis = mat

        gizmo.hide = not ob.visible_get()

    @classmethod
    def create_gizmos(cls, ob, gizmo_group):
        bounds_gizmo = gizmo_group.gizmos.new(PortalBoundsGizmo.bl_idname)
        setattr(bounds_gizmo, "hubs_gizmo_shape", box.SHAPE)
        bounds_gizmo.setup()
        bounds_gizmo.use_draw_scale = False
        bounds_gizmo.use_draw_modal = False
        bounds_gizmo.color = (0.5, 0.5, 0.0)
        bounds_gizmo.alpha = 0.5
        bounds_gizmo.scale_basis = 1.0
        bounds_gizmo.hide_select = True
        bounds_gizmo.color_highlight = (0.5, 0.5, 0.0)
        bounds_gizmo.alpha_highlight = 0.5

        bounds_gizmo.target_set_prop(
            "bounds", ob.hubs_component_portal, "bounds")
        bounds_gizmo.target_set_prop(
            "offset", ob.hubs_component_portal, "offset")

        portal_gizmo = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        setattr(portal_gizmo, "hubs_gizmo_shape", portal.SHAPE)
        portal_gizmo.setup()
        portal_gizmo.use_draw_scale = False
        portal_gizmo.use_draw_modal = False
        portal_gizmo.color = (0.8, 0.5, 0.0)
        portal_gizmo.alpha = 0.5
        portal_gizmo.scale_basis = 1.0
        portal_gizmo.hide_select = True
        portal_gizmo.color_highlight = (0.8, 0.5, 0.0)
        portal_gizmo.alpha_highlight = 0.5

        return [bounds_gizmo, portal_gizmo]

    @staticmethod
    def register():
        bpy.utils.register_class(PortalBoundsGizmo)

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(PortalBoundsGizmo)
