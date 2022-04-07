import bpy
from bpy.props import PointerProperty, EnumProperty
from bpy.types import Image
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ... import io
import math


resolutions = [
    (128, 64),
    (256, 128),
    (512, 256),
    (1024, 512),
    (2048, 1024)
]

probe_baking = False


class BakeProbeOperator(bpy.types.Operator):
    bl_idname = "render.hubs_render_reflection_probe"
    bl_label = "Render Hubs Reflection Probe"

    _timer = None
    done = False
    cancelled = False
    probe = None

    @classmethod
    def poll(cls, context):
        return not probe_baking

    def render_post(self, scene, depsgraph):
        print("Finished render")
        self.done = True

    def render_cancelled(self, scene, depsgraph):
        print("Render canceled")
        self.cancelled = True

    def execute(self, context):
        global probe_baking

        bpy.app.handlers.render_post.append(self.render_post)
        bpy.app.handlers.render_cancel.append(self.render_cancelled)

        self._timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        context.window_manager.modal_handler_add(self)

        probe_baking = True
        self.probe = context.object

        self.camera_data = bpy.data.cameras.new(name='Temp EnvMap Camera')
        camera_object = bpy.data.objects.new(
            'Temp EnvMap Camera', self.camera_data)
        bpy.context.scene.collection.objects.link(camera_object)

        return render_probe(self.probe, self.camera_data, camera_object)

    def modal(self, context, event):
        global probe_baking

        # print("ev: %s" % event.type)
        if event.type == 'TIMER' and (self.cancelled or self.done):
            bpy.app.handlers.render_post.remove(self.render_post)
            bpy.app.handlers.render_cancel.remove(self.render_cancelled)
            context.window_manager.event_timer_remove(self._timer)

            bpy.data.cameras.remove(self.camera_data)

            probe_baking = False

            if self.cancelled:
                return {"CANCELLED"}

            image_name = "generated_cubemap-%s" % self.probe.name
            img = bpy.data.images.get(image_name)
            if not img:
                img = bpy.data.images.load(
                    filepath=bpy.context.scene.render.filepath)
                img.name = image_name
            else:
                img.reload()

            self.probe.hubs_component_reflection_probe['envMapTexture'] = img

            return {"FINISHED"}

        return {"PASS_THROUGH"}


def render_probe(probe, camera_data, camera_object):
    try:
        camera_data.type = "PANO"
        camera_data.cycles.panorama_type = "EQUIRECTANGULAR"

        camera_data.cycles.longitude_min = -math.pi
        camera_data.cycles.longitude_max = math.pi
        camera_data.cycles.latitude_min = -math.pi/2
        camera_data.cycles.latitude_max = math.pi/2

        camera_data.clip_start = probe.data.clip_start
        camera_data.clip_end = probe.data.clip_end

        camera_object.matrix_world = probe.matrix_world.copy()
        camera_object.rotation_euler.x += math.pi/2
        camera_object.rotation_euler.z += -math.pi/2

        bpy.context.scene.camera = camera_object
        bpy.context.scene.render.engine = "CYCLES"
        (x, y) = resolutions[probe.hubs_component_reflection_probe.get(
            'resolution', 1)]
        bpy.context.scene.render.resolution_x = x
        bpy.context.scene.render.resolution_y = y
        bpy.context.scene.render.image_settings.file_format = "HDR"
        bpy.context.scene.render.filepath = "//generated_cubemaps/%s.hdr" % probe.name

        # TODO don't clobber renderer properties
        # TODO handle skipping compositor

        tmp_pref = bpy.context.preferences.view.render_display_type
        bpy.context.preferences.view.render_display_type = "NONE"
        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
        bpy.context.preferences.view.render_display_type = tmp_pref

        return {"RUNNING_MODAL"}

    except Exception as e:
        print(e)
        return {"CANCELLED"}


class hubs_component_reflection_probe(HubsComponent):
    _definition = {
        'export_name': 'reflection-probe',
        'display_name': 'Reflection Probe',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'pane_type': PanelType.OBJECT_DATA
    }

    envMapTexture: PointerProperty(
        name="EnvMap",
        description="An equirectangular image to use as the environment map for this probe",
        type=Image
    )

    resolution: EnumProperty(
        name='Resolution',
        description='Resolution for the environment map',
        items=[
            ('128x64', '128x64', '128 x 64'),
            ('256x128', '256x128', '256 x 128'),
            ('512x256', '512x256', '512 x 256'),
            ('1024x512', '1024x512', '1024 x 512'),
            ('2048x1024', '2048x1024', '2048 x 1024'),
        ],
        default='256x128'
    )

    def draw(self, col):
        HubsComponent.draw(self, col)

        col.operator(
            "render.hubs_render_reflection_probe",
            text="Bake"
        )

    def gather(self, export_settings, object):
        return {
            "size": object.data.influence_distance,
            "envMapTexture": {
                "__mhc_link_type": "texture",
                "index": io.utils.gather_texture(self.envMapTexture, export_settings)
            }
        }

    @classmethod
    def poll(cls, context):
        return context.object.type == 'LIGHT_PROBE'

    @staticmethod
    def register():
        bpy.utils.register_class(BakeProbeOperator)
        pass

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(BakeProbeOperator)
        pass
