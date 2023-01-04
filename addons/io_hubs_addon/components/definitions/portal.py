import bpy
from bpy.props import FloatVectorProperty, PointerProperty, StringProperty, EnumProperty
from bpy.types import Image
from ..gizmos import bone_matrix_world, CustomModelGizmo
from ..models import portal, box
from ..types import Category, PanelType, NodeType
from ..hubs_component import HubsComponent
from ..utils import has_component
from mathutils import Matrix
from bpy.types import (Gizmo, Object)
from ...io.utils import delayed_gather
import uuid


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


def filter_on_component(self, ob):
    return has_component(ob, Portal.get_name()) and self.name != ob.hubs_component_portal.name


class Portal(HubsComponent):
    _definition = {
        'name': 'portal',
        'display_name': 'Portal',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MESH_CIRCLE',
    }

    name: StringProperty(
        name="Name",
        description="The name of the portal that will be shown int he tag",
        default="Portal"
    )

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

    target_local: PointerProperty(
        name="Target",
        description="The other end of this portal",
        type=Object,
        poll=filter_on_component)

    target_remote: StringProperty(
        name="Target",
        description="A url that pointing to another portal or waypoint")

    image: PointerProperty(
        name="Image",
        description="An image of the remote portal to show on this portal",
        type=Image
    )

    uuid: StringProperty(
        name="Id",
        description="Portal Id",
        options={'HIDDEN'}
    )

    type: EnumProperty(
        name="Type",
        description="Portal Type",
        items=[("local", "Local", "A portal whose target portal is in the same room"),
               ("remove", "Remote", "A portal whose target portal is in a different room")],
        default="local")

    @classmethod
    def init(cls, obj):
        obj.hubs_component_portal.name = obj.name
        obj.hubs_component_portal.uuid = str(uuid.uuid4()).upper()

    @ classmethod
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

    @ classmethod
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

    @ staticmethod
    def register():
        bpy.utils.register_class(PortalBoundsGizmo)

    @ staticmethod
    def unregister():
        bpy.utils.unregister_class(PortalBoundsGizmo)

    def draw(self, context, layout, panel):
        layout.prop(data=self, property="name")
        layout.prop(data=self, property="type")
        if self.type == 'local':
            layout.prop(data=self, property="target_local")
        else:
            layout.prop(data=self, property="target_remote")
            layout.prop(data=self, property="image")
        layout.prop(data=self, property="bounds")
        layout.prop(data=self, property="offset")

    @delayed_gather
    def gather(self, export_settings, object):
        bounds = {
            'x': self.bounds.x,
            'y': self.bounds.y,
            'z': self.bounds.z
        }
        offset = {
            'x': self.offset.x,
            'y': self.offset.y,
            'z': self.offset.z
        }
        if export_settings['gltf_yup']:
            bounds['y'] = self.bounds.z
            bounds['z'] = self.bounds.y
            offset['y'] = self.offset.z
            offset['z'] = -self.offset.y

        from ...io.utils import gather_texture_property
        return {
            'uuid': self.uuid,
            'bounds': bounds,
            'offset': offset,
            'name': self.name,
            'target': self.target_local.hubs_component_portal.uuid if self.type == 'local' else self.target_remote,
            'image': gather_texture_property(
                export_settings,
                object,
                self,
                'image'),
            'local': self.type == 'local'
        }
