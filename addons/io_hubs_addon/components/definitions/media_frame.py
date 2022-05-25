import bpy
from bpy.props import EnumProperty, FloatVectorProperty, BoolProperty
from bpy.types import Node
from ..gizmos import CustomModelGizmo
from ..models import box
from ..hubs_component import HubsComponent
from ..types import Category, PanelType
from mathutils import Matrix, Vector
from .networked import migrate_networked
from bpy.app.handlers import persistent


def get_gizmo_scale(ob):
    if ob.type == 'MESH':
        return ob.dimensions.copy() / 2
    else:
        return ob.scale.copy() * ob.empty_display_size


def get_gizmo_dimension(ob):
    if ob.type == 'MESH':
        return ob.dimensions.copy()
    else:
        return ob.scale.copy() * ob.empty_display_size * 2


def update_object_bounds(self, context):
    ob = context.object
    if ob.type == 'MESH':
        ob.dimensions = self.bounds.copy()
    else:
        ob.scale = self.bounds.copy() / ob.empty_display_size / 2


@persistent
def update_bounds_handler(dummy):
    ob = bpy.context.object
    if ob and MediaFrame.get_name() in ob.hubs_component_list.items:
        ob.hubs_component_media_frame.bounds = get_gizmo_dimension(ob)


class MediaFrame(HubsComponent):
    _definition = {
        'name': 'media-frame',
        'display_name': 'Media Frame',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'OBJECT_DATA',
        'deps': ['networked']
    }

    bounds: FloatVectorProperty(
        name="Bounds",
        description="Bounding box to fit objects into when they are snapped into the media frame.",
        unit='LENGTH',
        subtype="XYZ_LENGTH",
        default=(2.0, 2.0, 2.0),
        update=update_object_bounds)

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
    def init(cls, ob):
        ob.hubs_component_media_frame.bounds = get_gizmo_dimension(ob)

    @classmethod
    def update_gizmo(cls, ob, gizmo):
        loc, rot, _ = ob.matrix_world.decompose()
        scale = get_gizmo_scale(ob)
        mat_out = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        gizmo.matrix_basis = mat_out
        gizmo.hide = not ob.visible_get()

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        widget = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        setattr(widget, "hubs_gizmo_shape", box.SHAPE)
        widget.setup()
        loc, rot, _ = ob.matrix_world.decompose()
        scale = get_gizmo_scale(ob)
        mat_out = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        widget.matrix_basis = mat_out
        widget.use_draw_scale = False
        widget.use_draw_modal = True
        widget.color = (0.0, 0.0, 0.8)
        widget.alpha = 1.0
        widget.hide = not ob.visible_get()
        widget.scale_basis = 1.0
        widget.hide_select = False
        widget.color_highlight = (0.0, 0.0, 0.8)
        widget.alpha_highlight = 0.5

        op = widget.target_set_operator("transform.resize")
        op.constraint_axis = False, False, False
        op.orient_type = 'LOCAL'
        op.release_confirm = True

        return widget

    @classmethod
    def migrate(cls):
        migrate_networked(cls.get_name())

    @staticmethod
    def register():
        if not update_bounds_handler in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(
                update_bounds_handler)

    @staticmethod
    def unregister():
        if update_bounds_handler in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(
                update_bounds_handler)

    def gather(self, export_settings, object):
        bounds = {
            'x': self.bounds.x / object.scale.x,
            'y': self.bounds.y / object.scale.y,
            'z': self.bounds.z / object.scale.z
        }
        if export_settings['gltf_yup']:
            bounds['y'] = self.bounds.z / object.scale.z
            bounds['z'] = self.bounds.y / object.scale.y

        return {
            'bounds': bounds,
            'mediaType': self.mediaType,
            'snapToCenter': self.snapToCenter
        }
