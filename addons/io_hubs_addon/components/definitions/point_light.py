from ..models import pointlight
from ..gizmos import CustomModelGizmo, bone_matrix_world
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class PointLight(HubsComponent):
    _definition = {
        'name': 'point-light',
        'display_name': 'Point Light',
        'category': Category.LIGHTS,
        'node_type': NodeType. NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'LIGHT_POINT',
        'version': (1, 0, 0)
    }

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR_GAMMA',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    intensity: FloatProperty(name="Intensity",
                             description="Intensity",
                             default=1.0)

    range: FloatProperty(name="Range",
                         description="Range",
                         default=1.0)

    decay: FloatProperty(name="Decay",
                         description="Decay",
                         default=1.0)

    castShadow: BoolProperty(
        name="Cast Shadow", description="Cast Shadow", default=True)

    shadowMapResolution: IntVectorProperty(name="Shadow Map Resolution",
                                           description="Shadow Map Resolution",
                                           size=2,
                                           default=[512, 512])

    shadowBias: FloatProperty(name="Shadow Bias",
                              description="Shadow Bias",
                              default=1.0)

    shadowRadius: FloatProperty(name="Shadow Radius",
                                description="Shadow Radius",
                                default=1.0)

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
        setattr(gizmo, "hubs_gizmo_shape", pointlight.SHAPE)
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
