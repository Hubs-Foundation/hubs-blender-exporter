from bpy.props import FloatVectorProperty
from ..hubs_component import HubsComponent
from ..gizmos import update_gizmos
from ..types import Category, PanelType, NodeType
from mathutils import Matrix, Quaternion
from math import radians


class Mirror(HubsComponent):
    _definition = {
        'name': 'mirror',
        'display_name': 'Mirror',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MOD_MIRROR',
        'version': (1, 0, 0),
        'tooltip': 'Add a mirror plane to the room'
    }

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR_GAMMA',
                               default=(0.498039, 0.498039, 0.498039),
                               size=3,
                               min=0,
                               max=1,
                               update=lambda self, context: update_gizmos())

    def draw(self, context, layout, panel_type):
        super().draw(context, layout, panel_type)

        cmp = getattr(context.object, self.get_id())
        if cmp.color[:] == (0.0, 0.0, 0.0):
            layout.label(
                text="You won't see much if the mirror is black", icon='ERROR')

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new('GIZMO_GT_primitive_3d')
        gizmo.draw_style = ('PLANE')
        gizmo.use_draw_scale = False
        gizmo.use_draw_offset_scale = True
        gizmo.line_width = 3
        gizmo.color = getattr(ob, cls.get_id()).color[:3]
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
            # Account for bones using Y up
            rot_offset = Matrix.Rotation(radians(-90), 4, 'X').to_4x4()
            rot = rot.normalized().to_matrix().to_4x4() @ rot_offset
            # Account for the armature object's position
            loc = ob.matrix_world @ Matrix.Translation(loc)
            # Apply the custom rotation
            rot_offset = Matrix.Rotation(radians(90), 4, 'X').to_4x4()
            rot = rot @ rot_offset
            # Shrink the gizmo to a 1x1m square (Blender defaults to 2x2m)
            scale = scale / 2
            # Convert the scale to a matrix
            scale = Matrix.Diagonal(scale).to_4x4()
            # Assemble the new matrix
            mat_out = loc @ rot @ scale

        else:
            loc, rot, scale = ob.matrix_world.decompose()
            # Apply the custom rotation
            offset = Quaternion((1.0, 0.0, 0.0), radians(90.0))
            new_rot = rot @ offset
            # Shrink the gizmo to a 1x1m square (Blender defaults to 2x2m)
            scale = scale / 2
            # Assemble the new matrix
            mat_out = Matrix.Translation(
                loc) @ new_rot.normalized().to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()

        gizmo.matrix_basis = mat_out
        gizmo.hide = not ob.visible_get()
