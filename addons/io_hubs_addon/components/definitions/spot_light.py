from ..models import spot_light
from ..gizmos import CustomModelGizmo, bone_matrix_world, update_gizmos
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from math import pi


class SpotLight(HubsComponent):
    _definition = {
        'name': 'spot-light',
        'display_name': 'Spot Light',
        'category': Category.LIGHTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'LIGHT_SPOT',
        'version': (1, 0, 0),
        'tooltip': 'Add a spot light'
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

    range: FloatProperty(name="Range",
                         description="Range",
                         default=0.0)

    decay: FloatProperty(name="Decay",
                         description="Decay",
                         default=1.0)

    innerConeAngle: FloatProperty(
        name="Cone Inner Angle",
        description="A double value describing the angle, in degrees, of a cone inside of which there will be no volume reduction",
        subtype="ANGLE",
        default=0.0,
        min=0.0,
        max=pi / 2)

    outerConeAngle: FloatProperty(
        name="Cone Outer Angle",
        description="A double value describing the angle, in degrees, of a cone outside of which the volume will be reduced by a constant value, defined by the coneOuterGain attribute",
        subtype="ANGLE",
        default=pi / 4,
        min=0.0,
        max=pi / 2)

    decay: FloatProperty(name="Decay",
                         description="Decay",
                         default=2.0)

    castShadow: BoolProperty(
        name="Cast Shadow", description="Cast Shadow", default=True)

    shadowMapResolution: IntVectorProperty(name="Shadow Map Resolution",
                                           description="Shadow Map Resolution",
                                           size=2,
                                           default=[512, 512])

    shadowBias: FloatProperty(name="Shadow Bias",
                              description="Shadow Bias",
                              default=0.0)

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
        setattr(gizmo, "hubs_gizmo_shape", spot_light.SHAPE)
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
