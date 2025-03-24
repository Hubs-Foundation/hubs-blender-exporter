from bpy.props import StringProperty, BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from mathutils import Matrix
from math import radians


class PDF(HubsComponent):
    _definition = {
        'name': 'pdf',
        'display_name': 'PDF',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['networked'],
        'icon': 'FILE_IMAGE',
        'version': (1, 0, 0),
        'tooltip': 'Load a PDF from a URL and show it in the scene.'
    }
    src: StringProperty(
        name="PDF URL", description="The web address of the PDF", default='https://example.org/PdfFile.pdf')
    controls: BoolProperty(
        name="Controls",
        description="When enabled, shows pagination buttons when hovering your cursor over it in Hubs that allow you to switch pages",
        default=True)

    @classmethod
    def gather_name(cls):
        return 'image'

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new('GIZMO_GT_primitive_3d')
        gizmo.draw_style = ('PLANE')
        gizmo.use_draw_scale = False
        gizmo.use_draw_offset_scale = True
        gizmo.line_width = 3
        gizmo.color = (0.8, 0.8, 0.8)
        gizmo.alpha = 0.5
        gizmo.hide_select = True
        gizmo.scale_basis = 0.5
        gizmo.use_draw_modal = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0
        return gizmo

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        if bone:
            loc, rot, scale = bone.matrix.to_4x4().decompose()
            # Account for the armature object's position
            loc = ob.matrix_world @ Matrix.Translation(loc)
            # Convert to A4 aspect ratio
            scale[1] = 1.414
            # Shrink the gizmo to fit within a 1x1m square
            scale = scale * 0.3538
            # Convert the scale to a matrix
            scale = Matrix.Diagonal(scale).to_4x4()
            # Convert the rotation to a matrix
            rot = rot.normalized().to_matrix().to_4x4()
            # Assemble the new matrix
            mat_out = loc @ rot @ scale
        else:
            loc, rot, scale = ob.matrix_world.decompose()
            # Apply the custom rotation
            rot_offset = Matrix.Rotation(radians(90), 4, 'X').to_4x4()
            new_rot = rot.normalized().to_matrix().to_4x4() @ rot_offset
            # Convert to A4 aspect ratio
            scale[1] = 1.414
            # Shrink the gizmo to fit within a 1x1m square
            scale = scale * 0.3538
            # Assemble the new matrix
            mat_out = Matrix.Translation(
                loc) @ new_rot @ Matrix.Diagonal(scale).to_4x4()
        gizmo.matrix_basis = mat_out
        gizmo.hide = not ob.visible_get()
