from bpy.props import EnumProperty, FloatVectorProperty, BoolProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
import mathutils
import bpy


class MediaFrame(HubsComponent):
    _definition = {
        'id': 'media-frame',
        'name': 'hubs_component_media_frame',
        'display_name': 'Media Frame',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'MOD_WIREFRAME'
    }

    bounds: FloatVectorProperty(
        name="Only Mods", description="Bounding box to fit objects into when they are snapped into the media frame.", unit='LENGTH', subtype="XYZ_LENGTH", default=(1.0, 1.0, 1.0))

    mediaType: EnumProperty(
        name="Media Type",
        description="Limit what type of media this frame will capture",
        items=[("all", "All Media", "Allow any type of media."),
               ("all-2d", "Only 2D Media", "Allow only Images, Videos, and PDFs."),
               ("model", "Only 3D Models", "Allow only 3D models."),
               ("image", "Only Images", "Allow only images."),
               ("video", "Only Videos", "Allow only videos."),
               ("pdf", "Only PDFs", "Allow only PDFs.")],
        default="all-2d")

    snapToCenter: BoolProperty(
        name="Snap To Center",
        description="Snap the media to the center of the media frame when capturing. If set to false the object will just remain in the place it was dorpped but still be considered \"captured\" by the media frame.",
        default=True
    )

    @classmethod
    def create_gizmo(cls, obj, gizmo_group):
        widget = gizmo_group.gizmos.new('GIZMO_GT_cage_3d')
        widget.draw_style = ('BOX')
        widget.matrix_basis = obj.matrix_world.normalized()
        widget.line_width = 3
        widget.color = (0.8, 0.8, 0.8)
        widget.alpha = 0.5
        widget.hide = not obj.visible_get()
        widget.hide_select = True
        widget.scale_basis = 1.0
        widget.use_draw_modal = True
        widget.color_highlight = (0.8, 0.8, 0.8)
        widget.alpha_highlight = 1.0

        op = widget.target_set_operator("transform.translate")
        op.constraint_axis = False, False, False
        op.orient_type = 'LOCAL'
        op.release_confirm = True

        def update(obj, gizmo):
            mat_scale = mathutils.Matrix.Scale(2.0, 4)
            gizmo.matrix_basis = obj.matrix_world @ mat_scale
            bpy.context.view_layer.update()

        return widget, update
