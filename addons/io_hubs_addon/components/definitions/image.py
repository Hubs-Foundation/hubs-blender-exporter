from ..models import image
from ..gizmos import CustomModelGizmo, bone_matrix_world
from bpy.props import EnumProperty, FloatProperty, StringProperty, BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..consts import PROJECTION_MODE, TRANSPARENCY_MODE
from .networked import migrate_networked


class Image(HubsComponent):
    _definition = {
        'name': 'image',
        'display_name': 'Image',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'FILE_IMAGE',
        'deps': ['networked'],
        'version': (1, 0, 0)
    }

    src: StringProperty(
        name="Image URL", description="The web address of the image", default="https://mozilla.org")

    controls: BoolProperty(
        name="Controls",
        description="When enabled, shows an \"open link\" button when hovering your cursor over it in Hubs that allows you to open the image in a new tab",
        default=True)

    alphaMode: EnumProperty(
        name="Transparency Mode",
        description="Transparency Mode",
        items=TRANSPARENCY_MODE,
        default="opaque")

    alphaCutoff: FloatProperty(
        name="Alpha Cutoff",
        description="Pixels with alpha values lower than this will be transparent on Binary transparency mode",
        default=0.5,
        min=0.0,
        max=1.0)

    projection: EnumProperty(
        name="Projection",
        description="Projection",
        items=PROJECTION_MODE,
        default="flat")

    def draw(self, context, layout, panel_type):
        layout.prop(self, "src")
        layout.prop(self, "controls")
        layout.prop(self, "alphaMode")
        if self.alphaMode == "mask":
            layout.prop(self, "alphaCutoff")
        layout.prop(self, "projection")

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            migrate_networked(host)

        return migration_occurred

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        if bone:
            mat = bone_matrix_world(ob, bone)
        else:
            mat = ob.matrix_world.copy()

        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        gizmo.object = ob
        setattr(gizmo, "hubs_gizmo_shape", image.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.color = (0.8, 0.8, 0.8)
        gizmo.alpha = 0.5
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0

        return gizmo
