from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, StringProperty, IntProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType, MigrationType
from ..consts import INTERPOLATION_MODES
from ..gizmos import CustomModelGizmo, bone_matrix_world, update_gizmos
from ..models import particle_emitter
from ..utils import is_linked, get_host_reference_message
import bpy
from mathutils import Vector
from ...io.utils import import_component, assign_property


class ParticleEmitter(HubsComponent):
    _definition = {
        'name': 'particle-emitter',
        'display_name': 'Particle Emitter',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'PARTICLES',
        'version': (1, 1, 0),
        'tooltip': 'Send forth a continuous stream of 2D billboarded images (particles). This can be used to approximate things like fire, rain, smoke, and other effects'
    }

    particleCount: IntProperty(
        name="Particle Count", description="Particle Count", subtype="UNSIGNED", default=100)

    src: StringProperty(
        name="Image Source", description="The web address (URL) of the image to use for each particle",
        default="https://assets.example.org/spoke/assets/images/dot-75db99b125fe4e9afbe58696320bea73.png")

    ageRandomness: FloatProperty(
        name="Age Randomness", description="Age Randomness", default=10.0)

    lifetime: FloatProperty(
        name="Lifetime", description="Lifetime", unit="TIME", subtype="TIME", default=5.0)

    lifetimeRandomness: FloatProperty(
        name="Lifetime Randomness", description="Lifetime Randomness", default=5.0)

    sizeCurve: EnumProperty(
        name="Size Curve",
        description="Size Curve",
        items=INTERPOLATION_MODES,
        default="linear")

    startSize: FloatProperty(
        name="Start Size", description="Start Size", default=0.25)

    endSize: FloatProperty(
        name="End Size", description="End Size", default=0.25)

    sizeRandomness: FloatProperty(
        name="Size Randomness", description="Size Randomness", default=0.0)

    colorCurve: EnumProperty(
        name="Color Curve",
        description="Color Curve",
        items=INTERPOLATION_MODES,
        default="linear")

    startColor: FloatVectorProperty(name="Start Color",
                                    description="Start Color",
                                    subtype='COLOR_GAMMA',
                                    default=(1.0, 1.0, 1.0, 1.0),
                                    size=4,
                                    min=0,
                                    max=1,
                                    update=lambda self, context: update_gizmos())

    startOpacity: FloatProperty(
        name="Start Opacity", description="Start Opacity", default=1.0)

    middleColor: FloatVectorProperty(name="Middle Color",
                                     description="Middle Color",
                                     subtype='COLOR_GAMMA',
                                     default=(1.0, 1.0, 1.0, 1.0),
                                     size=4,
                                     min=0,
                                     max=1)

    middleOpacity: FloatProperty(
        name="Middle Opacity", description="Middle Opacity", default=1.0)

    endColor: FloatVectorProperty(name="End Color",
                                  description="End Color",
                                  subtype='COLOR_GAMMA',
                                  default=(1.0, 1.0, 1.0, 1.0),
                                  size=4,
                                  min=0,
                                  max=1)

    endOpacity: FloatProperty(
        name="End Opacity", description="end Opacity", default=1.0)

    velocityCurve: EnumProperty(
        name="Velocity Curve",
        description="Velocity Curve",
        items=INTERPOLATION_MODES,
        default="linear")

    startVelocity: FloatVectorProperty(
        name="Start Velocity", description="Start Velocity", unit="LENGTH", subtype="XYZ", default=(0.0, 0.0, 0.5))

    endVelocity: FloatVectorProperty(
        name="End Velocity", description="End Velocity", unit="LENGTH", subtype="XYZ", default=(0.0, 0.0, 0.5))

    angularVelocity: FloatProperty(
        name="Angular Velocity", description="Angular Velocity", unit="VELOCITY", default=0.0)

    def draw(self, context, layout, panel):
        alert_src = getattr(self, "src") == self.bl_rna.properties['src'].default
        for key in self.get_properties():
            if not self.bl_rna.properties[key].is_hidden:
                row = layout.row()
                if key == "src" and alert_src:
                    row.alert = True
                row.prop(data=self, property=key)
                if key == "src" and alert_src:
                    warning_row = layout.row()
                    warning_row.alert = True
                    warning_row.label(
                        text="Warning: the default URL won't work unless you replace 'example.org' with the domain of your Hubs instance.",
                        icon='ERROR')

    def gather(self, export_settings, object):
        props = super().gather(export_settings, object)
        props['startVelocity'] = {
            'x': self.startVelocity[0],
            'y': self.startVelocity[2] if export_settings['gltf_yup'] else self.startVelocity[1],
            'z': self.startVelocity[1] if export_settings['gltf_yup'] else self.startVelocity[2],
        }
        props['endVelocity'] = {
            'x': self.endVelocity[0],
            'y': self.endVelocity[2] if export_settings['gltf_yup'] else self.endVelocity[1],
            'z': self.endVelocity[1] if export_settings['gltf_yup'] else self.endVelocity[2],
        }
        return props

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 1, 0):
            migration_occurred = True
            startVelocity = self.startVelocity.copy()
            startVelocity = Vector((startVelocity.x, startVelocity.z, startVelocity.y))
            self.startVelocity = startVelocity

            endVelocity = self.endVelocity.copy()
            endVelocity = Vector((endVelocity.x, endVelocity.z, endVelocity.y))
            self.endVelocity = endVelocity

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
        setattr(gizmo, "hubs_gizmo_shape", particle_emitter.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.color = getattr(ob, cls.get_id()).startColor[:3]
        gizmo.alpha = 0.5
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0

        return gizmo

    @classmethod
    def gather_import(cls, gltf, blender_host, component_name, component_value, import_report, blender_ob=None):
        blender_component = import_component(
            component_name, blender_host)

        gltf_yup = gltf.import_settings.get('gltf_yup', True)

        for property_name, property_value in component_value.items():
            if property_name in ['startVelocity', 'endVelocity'] and gltf_yup:
                property_value['y'], property_value['z'] = property_value['z'], property_value['y']

            assign_property(gltf.vnodes, blender_component,
                            property_name, property_value)
