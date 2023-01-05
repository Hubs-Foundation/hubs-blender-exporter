from ..models import directional_light
from ..gizmos import CustomModelGizmo, bone_matrix_world, update_gizmos
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType


class DirectionalLight(HubsComponent):
    _definition = {
        'name': 'directional-light',
        'display_name': 'Directional Light',
        'category': Category.LIGHTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'LIGHT_SUN',
        'version': (1, 0, 0)
    }

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR_GAMMA',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1,
                               update=lambda self, context: update_gizmos())

    intensity: FloatProperty(name="Intensity",
                             description="Intensity",
                             default=1.0)

    castShadow: BoolProperty(name="Cast Shadow", default=True)

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
        setattr(gizmo, "hubs_gizmo_shape", directional_light.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.color = getattr(ob, cls.get_id()).color[:3]
        gizmo.alpha = 0.5
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0

        return gizmo
