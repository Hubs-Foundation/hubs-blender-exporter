from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, StringProperty, IntProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType
from ..consts import INTERPOLATION_MODES
from ..gizmos import CustomModelGizmo, bone_matrix_world
from ..models import particle_emitter


class ParticleEmitter(HubsComponent):
    _definition = {
        'name': 'particle-emitter',
        'display_name': 'Particle Emitter',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'PARTICLES',
        'version': (1, 0, 0)
    }

    src: StringProperty(
        name="Image Source", description="The web address (URL) of the image to use for each particle",
        default="https://mozilla.org")

    startColor: FloatVectorProperty(name="Start Color",
                                    description="Start Color",
                                    subtype='COLOR_GAMMA',
                                    default=(1.0, 1.0, 1.0, 1.0),
                                    size=4,
                                    min=0,
                                    max=1)

    middleColor: FloatVectorProperty(name="Middle Color",
                                     description="Middle Color",
                                     subtype='COLOR_GAMMA',
                                     default=(1.0, 1.0, 1.0, 1.0),
                                     size=4,
                                     min=0,
                                     max=1)

    endColor: FloatVectorProperty(name="End Color",
                                  description="End Color",
                                  subtype='COLOR_GAMMA',
                                  default=(1.0, 1.0, 1.0, 1.0),
                                  size=4,
                                  min=0,
                                  max=1)

    startOpacity: FloatProperty(
        name="Start Opacity", description="Start Opacity", default=1.0)

    middleOpacity: FloatProperty(
        name="Middle Opacity", description="Middle Opacity", default=1.0)

    endOpacity: FloatProperty(
        name="End Opacity", description="end Opacity", default=1.0)

    sizeCurve: EnumProperty(
        name="Size Curve",
        description="Size Curve",
        items=INTERPOLATION_MODES,
        default="linear")

    colorCurve: EnumProperty(
        name="Color Curve",
        description="Color Curve",
        items=INTERPOLATION_MODES,
        default="linear")

    startSize: FloatProperty(
        name="Start Size", description="Start Size", default=0.25)

    endSize: FloatProperty(
        name="End Size", description="End Size", default=0.25)

    sizeRandomness: FloatProperty(
        name="Size Randomness", description="Size Randomness", default=0.0)

    ageRandomness: FloatProperty(
        name="Age Randomness", description="Age Randomness", default=10.0)

    lifetime: FloatProperty(
        name="Lifetime", description="Lifetime", unit="TIME", subtype="TIME", default=5.0)

    lifetimeRandomness: FloatProperty(
        name="Lifetime Randomness", description="Lifetime Randomness", default=5.0)

    particleCount: IntProperty(
        name="Particle Count", description="Particle Count", subtype="UNSIGNED", default=100)

    startVelocity: FloatVectorProperty(
        name="Start Velocity", description="Start Velocity", unit="VELOCITY", subtype="XYZ", default=(0.0, 0.0, 0.5))

    endVelocity: FloatVectorProperty(
        name="End Velocity", description="End Velocity", unit="VELOCITY", subtype="XYZ", default=(0.0, 0.0, 0.0))

    velocityCurve: EnumProperty(
        name="Velocity Curve",
        description="Velocity Curve",
        items=INTERPOLATION_MODES,
        default="linear")

    angularVelocity: FloatProperty(
        name="Angular Velocity", description="Angular Velocity", unit="VELOCITY", default=0.0)

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
        setattr(gizmo, "hubs_gizmo_shape", particle_emitter.SHAPE)
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
