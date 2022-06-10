import bpy
from bpy.props import EnumProperty, FloatVectorProperty, BoolProperty
from bpy.types import (Gizmo)
from ..gizmos import process_input_axis
from ..models import box
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import V_S1
from .networked import migrate_networked
from mathutils import Matrix, Vector


class MediaFrameGizmo(Gizmo):
    """MediaFrame gizmo"""
    bl_idname = "GIZMO_GT_hba_mediaframe_gizmo"
    bl_target_properties = (
        {"id": "bounds", "type": 'FLOAT', "array_length": 3},
    )

    __slots__ = (
        "object",
        "hubs_gizmo_shape",
        "custom_shape",
        "init_mouse_y",
        "init_value",
        "out_value",
        "axis_state",
    )

    def _update_offset_matrix(self):
        loc, rot, _ = self.matrix_basis.decompose()
        scale = self.target_get_value("bounds")
        mat_out = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        self.matrix_basis = mat_out

    def draw(self, context):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def invoke(self, context, event):
        self.init_mouse_y = event.mouse_y
        self.init_value = Vector(self.target_get_value("bounds"))
        self.out_value = Vector(self.target_get_value("bounds"))
        self.axis_state = Vector((False, False, False))

        if not hasattr(self, "object") or not context.mode == 'OBJECT':
            return {'CANCELLED'}

        if not event.shift:
            bpy.ops.object.select_all(action='DESELECT')
        self.object.select_set(True)
        bpy.context.view_layer.objects.active = self.object

        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        context.area.header_text_set(None)
        if cancel:
            self.target_set_value("bounds", self.init_value)

    def modal(self, context, event, tweak):
        if event.type == 'ESC':
            return {'FINISHED'}

        delta = (event.mouse_y - self.init_mouse_y) / 100.0
        if 'SNAP' in tweak:
            delta = round(delta)
        if 'PRECISE' in tweak:
            delta /= 10.0

        self.out_value.xyz = self.init_value.xyz
        process_input_axis(event,
                           self.out_value,
                           delta,
                           self.axis_state)

        self.target_set_value("bounds", self.out_value)

        context.area.header_text_set(
            "Bounds %.4f %.4f %.4f" % self.out_value.to_tuple())

        return {'RUNNING_MODAL'}

    def setup(self):
        if hasattr(self, "hubs_gizmo_shape"):
            self.custom_shape = self.new_custom_shape(
                'TRIS', self.hubs_gizmo_shape)


class MediaFrame(HubsComponent):
    _definition = {
        'name': 'media-frame',
        'display_name': 'Media Frame',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'OBJECT_DATA',
        'deps': ['networked']
    }

    bounds: FloatVectorProperty(
        name="Bounds",
        description="Bounding box to fit objects into when they are snapped into the media frame.",
        unit='LENGTH',
        subtype="XYZ",
        default=(1.0, 1.0, 1.0))

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
    def update_gizmo(cls, ob, gizmo):
        loc, rot, _ = ob.matrix_world.decompose()
        scale = gizmo.target_get_value("bounds")
        mat_out = Matrix.Translation(
            loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()
        gizmo.matrix_basis = mat_out
        gizmo.hide = not ob.visible_get()

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        widget = gizmo_group.gizmos.new(MediaFrameGizmo.bl_idname)
        widget.object = ob
        setattr(widget, "hubs_gizmo_shape", box.SHAPE)
        widget.setup()
        widget.use_draw_scale = False
        widget.use_draw_modal = True
        widget.color = (0.0, 0.0, 0.8)
        widget.alpha = 1.0
        widget.hide = not ob.visible_get()
        widget.scale_basis = 1.0
        widget.hide_select = False
        widget.color_highlight = (0.0, 0.0, 0.8)
        widget.alpha_highlight = 0.5

        widget.target_set_prop(
            "bounds", ob.hubs_component_media_frame, "bounds")

        return widget

    @classmethod
    def migrate(cls, version):
        migrate_networked(cls.get_name())

        if version[1] < 1:
            for ob in bpy.data.objects:
                if cls.get_name() in ob.hubs_component_list.items:
                    bounds = ob.hubs_component_media_frame.bounds.copy()
                    bounds = Vector((bounds.x, bounds.z, bounds.y))
                    ob.hubs_component_media_frame.bounds = bounds

    @staticmethod
    def register():
        bpy.utils.register_class(MediaFrameGizmo)

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(MediaFrameGizmo)

    def gather(self, export_settings, object):
        bounds = {
            'x': self.bounds.x,
            'y': self.bounds.y,
            'z': self.bounds.z
        }
        if export_settings['gltf_yup']:
            bounds['y'] = self.bounds.z
            bounds['z'] = self.bounds.y

        return {
            'bounds': bounds,
            'mediaType': self.mediaType,
            'snapToCenter': self.snapToCenter
        }

    def draw(self, context, layout):
        super().draw(context, layout)

        parents = [context.object]
        while parents:
            parent = parents.pop()
            if parent.scale != V_S1:
                col = layout.column()
                col.alert = True
                col.label(
                    text="The media-frame object, and it's parents, scale needs to be [1,1,1]", icon='ERROR')

                break

            if parent.parent:
                parents.insert(0, parent.parent)

            if hasattr(parent, 'parent_bone') and parent.parent_bone:
                parents.insert(0, parent.parent.pose.bones[parent.parent_bone])
