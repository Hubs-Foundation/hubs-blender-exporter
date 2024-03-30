import bpy
from bpy.props import EnumProperty, FloatVectorProperty, BoolProperty
from bpy.types import (Gizmo, Bone, EditBone)
from ..gizmos import bone_matrix_world
from ..models import box
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType, MigrationType
from ..utils import V_S1, is_linked, get_host_reference_message
from .networked import migrate_networked
from mathutils import Matrix, Vector
from ...io.utils import import_component, assign_property


def is_bone(ob):
    return type(ob) == EditBone or type(ob) == Bone


class MediaFrameGizmo(Gizmo):
    """MediaFrame gizmo"""
    bl_idname = "GIZMO_GT_hba_mediaframe_gizmo"
    bl_target_properties = (
        {"id": "bounds", "type": 'FLOAT', "array_length": 3},
    )

    __slots__ = (
        "hubs_gizmo_shape",
        "custom_shape",
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
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'OBJECT_DATA',
        'deps': ['networked'],
        'version': (1, 0, 0)
    }

    mediaType: EnumProperty(
        name="Media Type",
        description="Limit what type of media this frame will capture",
        items=[("all", "All Media", "Allow any type of media"),
               ("all-2d", "Only 2D Media", "Allow only Images, Videos, and PDFs"),
               ("model", "Only 3D Models", "Allow only 3D models"),
               ("image", "Only Images", "Allow only images"),
               ("video", "Only Videos", "Allow only videos"),
               ("pdf", "Only PDFs", "Allow only PDFs")],
        default="all-2d")

    bounds: FloatVectorProperty(
        name="Bounds",
        description="Bounding box to fit objects into when they are snapped into the media frame",
        unit='LENGTH',
        subtype="XYZ",
        default=(1.0, 1.0, 1.0))

    alignX: EnumProperty(
        name="Align X",
        description="Media alignment along the X axis",
        items=[("min", "Min", "Align minimum X bounds of media and frame"),
               ("center", "Center", "Align X centers of media and frame"),
               ("max", "Max", "Align maximum X bounds of media and frame")],
        default="center")

    alignY: EnumProperty(
        name="Align Y",
        description="Media alignment along the Y axis",
        items=[("min", "Min", "Align minimum Y bounds of media and frame"),
               ("center", "Center", "Align Y centers of media and frame"),
               ("max", "Max", "Align maximum Y bounds of media and frame")],
        default="center")

    alignZ: EnumProperty(
        name="Align Z",
        description="Media alignment along the Z axis",
        items=[("min", "Min", "Align minimum Z bounds of media and frame"),
               ("center", "Center", "Align Z centers of media and frame"),
               ("max", "Max", "Align maximum Z bounds of media and frame")],
        default="center")

    scaleToBounds: BoolProperty(
        name="Scale To Bounds",
        description="Scale the media to fit within the bounds of the media frame",
        default=True
    )

    snapToCenter: BoolProperty(
        name="Snap To Center",
        description="Snap the media to the center of the media frame when capturing. If set to false the object will just remain in the place it was dropped but still be considered \"captured\" by the media frame",
        default=True
    )

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        gizmo.target_set_prop(
            "bounds", target.hubs_component_media_frame, "bounds")

        scale = gizmo.target_get_value("bounds")
        if bone:
            mat = bone_matrix_world(ob, bone, scale)
        else:
            loc, rot, _ = ob.matrix_world.decompose()
            mat = Matrix.Translation(
                loc) @ rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()

        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new(MediaFrameGizmo.bl_idname)
        setattr(gizmo, "hubs_gizmo_shape", box.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.color = (0.0, 0.0, 0.8)
        gizmo.alpha = 1.0
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.0, 0.0, 0.8)
        gizmo.alpha_highlight = 0.5

        gizmo.target_set_prop(
            "bounds", ob.hubs_component_media_frame, "bounds")

        return gizmo

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)
            bounds = self.bounds.copy()
            bounds = Vector((bounds.x, bounds.z, bounds.y))
            self.bounds = bounds

            if migration_type != MigrationType.GLOBAL or is_linked(ob) or type(ob) == bpy.types.Armature:
                host_reference = get_host_reference_message(panel_type, host, ob=ob)
                migration_report.append(
                    f"Warning: The Media Frame component's Y and Z bounds on the {panel_type.value} {host_reference} may not have migrated correctly")

        return migration_occurred

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
        align = {
            'x': self.alignX,
            'y': self.alignY,
            'z': self.alignZ
        }
        if export_settings['gltf_yup']:
            align['y'] = self.alignZ
            align['z'] = "min" if self.alignY == "max" else "max" if self.alignY == "min" else self.alignY
        return {
            'bounds': bounds,
            'mediaType': self.mediaType,
            'align': align,
            'scaleToBounds': self.scaleToBounds,
            'snapToCenter': self.snapToCenter
        }

    def draw(self, context, layout, panel):
        super().draw(context, layout, panel)

        parents = [context.object]
        while parents:
            parent = parents.pop()
            if parent.scale != V_S1:
                col = layout.column()
                col.alert = True
                col.label(
                    text="The media-frame object, and its parents' scale need to be [1,1,1]", icon='ERROR')

                break

            if parent.parent:
                parents.insert(0, parent.parent)

            if hasattr(parent, 'parent_bone') and parent.parent_bone:
                parents.insert(0, parent.parent.pose.bones[parent.parent_bone])

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, blender_ob=None):
        blender_component = import_component(
            component_name, blender_host)

        gltf_yup = gltf.import_settings.get('gltf_yup', True)

        for property_name, property_value in component_value.items():
            if property_name == 'bounds' and gltf_yup:
                property_value['y'], property_value['z'] = property_value['z'], property_value['y']

            assign_property(gltf.vnodes, blender_component,
                            property_name, property_value)
