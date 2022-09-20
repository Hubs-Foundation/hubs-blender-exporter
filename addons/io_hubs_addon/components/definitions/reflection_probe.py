import bpy
from bpy.props import PointerProperty, EnumProperty, StringProperty, BoolProperty
from bpy.types import Image, PropertyGroup

from ...components.utils import is_gpu_available

from ...preferences import get_addon_pref

from ..components_registry import get_components_registry
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ... import io
from ...utils import rgetattr, rsetattr
import math


DEFAULT_RESOLUTION_ITEMS = [
    ('128x64', '128x64',
     '128 x 64', '', 0),
    ('256x128', '256x128',
     '256 x 128', '', 1),
    ('512x256', '512x256',
     '512 x 256', '', 2),
    ('1024x512', '1024x512',
     '1024 x 512', '', 3),
    ('2048x1024', '2048x1024',
     '2048 x 1024', '', 4),
]

RESOLUTION_ITEMS = DEFAULT_RESOLUTION_ITEMS[:]

probe_baking = False
bake_mode = None


def get_resolutions(self, context):
    global RESOLUTION_ITEMS
    env_map = context.scene.hubs_component_environment_settings.envMapTexture
    if env_map:
        x = env_map.size[0]
        y = env_map.size[1]
        RESOLUTION_ITEMS = [(f'{x}x{y}', f'{x}x{y}', f'{x} x {y}', '', 0)]
    else:
        RESOLUTION_ITEMS = DEFAULT_RESOLUTION_ITEMS

    return RESOLUTION_ITEMS


def get_resolution(self):
    env_map = bpy.context.scene.hubs_component_environment_settings.envMapTexture
    list_ids = [x[0] for x in RESOLUTION_ITEMS]
    return 0 if env_map else list_ids.index(self.resolution_id)


def set_resolution(self, value):
    env_map = bpy.context.scene.hubs_component_environment_settings.envMapTexture
    if not env_map:
        self.resolution_id = RESOLUTION_ITEMS[value][0]


def get_probes():
    probes = []
    for ob in bpy.context.view_layer.objects:
        component_list = ob.hubs_component_list

        registered_hubs_components = get_components_registry()

        if component_list.items:
            for component_item in component_list.items:
                component_name = component_item.name
                if component_name in registered_hubs_components:
                    if component_name == 'reflection-probe':
                        probes.append(ob)

    return probes


class ReflectionProbeSceneProps(PropertyGroup):
    resolution: EnumProperty(name='Resolution',
                             description='Reflection Probe Selected Environment Map Resolution',
                             items=get_resolutions,
                             get=get_resolution,
                             set=set_resolution)

    render_resolution: StringProperty(name='Last Bake Resolution',
                                      description='Reflection Probe Last Bake Environment Map Resolution',
                                      options={'HIDDEN'},
                                      default='256x128')

    resolution_id: StringProperty(name='Current Resolution Id',
                                  default='256x128', options={'HIDDEN'})

    use_compositor: BoolProperty(name="Use Compositor",
        description="Controls whether the baked images will be processed by the compositor after baking",
        default=False
    )


class BakeProbeOperator(bpy.types.Operator):
    bl_idname = "render.hubs_render_reflection_probe"
    bl_label = "Render Hubs Reflection Probe"

    _timer = None
    done = False
    rendering = False
    cancelled = False
    probes = []
    probe_index = 0
    post_render_wait = 0

    bake_mode: EnumProperty(
        name="bake_mode",
        items=[('ACTIVE', 'Bake Active', 'Bake Active'),
               ('SELECTED', 'Bake Selected', 'Bake Selected'),
               ('ALL', 'Bake All', 'Bake All')],
        default='ACTIVE')

    @ classmethod
    def poll(cls, context):
        return not probe_baking and hasattr(bpy.context.scene, "cycles")

    def render_post(self, scene, depsgraph):
        print("Finished render")

        self.rendering = False

        if self.probe_index == 0:
            self.done = True
        else:
            self.probe_index -= 1

    def render_cancelled(self, scene, depsgraph):
        print("Render canceled")
        self.cancelled = True

    def execute(self, context):
        if self.bake_mode == 'SELECTED' and len(context.selected_objects) == 0:
            def draw(self, context):
                self.layout.label(
                    text="No objects selected to bake. Please select some objects first.")
            bpy.context.window_manager.popup_menu(
                draw, title="No object selected", icon='ERROR')
            return {"FINISHED"}

        bpy.app.handlers.render_post.append(self.render_post)
        bpy.app.handlers.render_cancel.append(self.render_cancelled)

        self._timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        context.window_manager.modal_handler_add(self)

        global probe_baking, bake_mode
        bake_mode = self.bake_mode

        self.camera_data = bpy.data.cameras.new(name='Temp EnvMap Camera')
        self.camera_object = bpy.data.objects.new(
            'Temp EnvMap Camera', self.camera_data)
        bpy.context.scene.collection.objects.link(self.camera_object)

        modes = {
            'ACTIVE': lambda: [context.active_object],
            'SELECTED': lambda: [ob for ob in get_probes() if ob in context.selected_objects],
            'ALL': lambda: get_probes(),
        }
        self.probes = modes[self.bake_mode]()

        self.saved_props = {}
        self.cancelled = False
        self.done = False
        self.rendering = False
        self.post_render_wait = 500
        self.probe_index = len(self.probes) - 1

        probe_baking = True

        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        global probe_baking

        # print("ev: %s" % event.type)
        if event.type == 'TIMER':
            if self.cancelled or self.done:
                probe_baking = False
                bpy.app.handlers.render_post.remove(self.render_post)
                bpy.app.handlers.render_cancel.remove(self.render_cancelled)
                context.window_manager.event_timer_remove(self._timer)

                bpy.context.scene.collection.objects.unlink(self.camera_object)
                bpy.data.cameras.remove(self.camera_data)

                self.restore_render_props()
                self.rendering = False

                if self.cancelled:
                    self.report(
                        {'WARNING'}, 'Reflection probe baking cancelled')
                    return {"CANCELLED"}

                for probe in self.probes:
                    image_name = "generated_cubemap-%s" % probe.name
                    img = bpy.data.images.get(image_name)
                    img_path = "%s/%s.hdr" % (get_addon_pref(context).tmp_path,
                                              probe.name)
                    if not img:
                        img = bpy.data.images.load(filepath=img_path)
                        img.name = image_name
                    else:
                        img.reload()
                    self.report(
                        {'INFO'}, 'Reflection probe environment map saved at %s' % img_path)

                    probe.hubs_component_reflection_probe['envMapTexture'] = img

                props = context.scene.hubs_scene_reflection_probe_properties
                props.render_resolution = props.resolution

                self.report({'INFO'}, 'Reflection probe baking finished')
                return {"FINISHED"}

            elif not self.rendering:
                # There seems to be some sort of deadlock if we don't wait some time time between renders.
                # It would be nice to get to the bottom of this.
                if self.post_render_wait < 500:
                    self.post_render_wait += 500
                    return {"PASS_THROUGH"}
                else:
                    self.post_render_wait = 0
                try:
                    self.rendering = True
                    self.render_probe(context)
                except Exception as e:
                    print(e)
                    self.cancelled = True
                    self.report(
                        {'ERROR'}, 'Reflection probe baking error %s' % e)

        return {"PASS_THROUGH"}

    def restore_render_props(self):
        for prop in self.saved_props:
           rsetattr(bpy.context, prop, self.saved_props[prop])

    def render_probe(self, context):
        probe = self.probes[self.probe_index]

        self.camera_data.type = "PANO"
        self.camera_data.cycles.panorama_type = "EQUIRECTANGULAR"

        self.camera_data.cycles.longitude_min = -math.pi
        self.camera_data.cycles.longitude_max = math.pi
        self.camera_data.cycles.latitude_min = -math.pi/2
        self.camera_data.cycles.latitude_max = math.pi/2

        self.camera_data.clip_start = probe.data.clip_start
        self.camera_data.clip_end = probe.data.clip_end

        self.camera_object.matrix_world = probe.matrix_world.copy()
        self.camera_object.rotation_euler.x += math.pi/2
        self.camera_object.rotation_euler.z += -math.pi/2

        resolution = context.scene.hubs_scene_reflection_probe_properties.resolution
        (x, y) = [int(i) for i in resolution.split('x')]
        output_path = "%s/%s.hdr" % (get_addon_pref(context).tmp_path, probe.name)
        use_compositor = context.scene.hubs_scene_reflection_probe_properties.use_compositor

        overrides = [
            ("preferences.view.render_display_type", "NONE"),
            ("scene.camera", self.camera_object),
            ("scene.render.engine", "CYCLES"),
            ("scene.cycles.device", "GPU" if is_gpu_available(context) else "CPU"),
            ("scene.render.resolution_x", x),
            ("scene.render.resolution_y", y),
            ("scene.render.resolution_percentage", 100),
            ("scene.render.image_settings.file_format", "HDR"),
            ("scene.render.filepath", output_path),
            ("scene.render.use_compositing", use_compositor),
            ("scene.use_nodes", use_compositor)
        ]

        for (prop, value) in overrides:
            if prop not in self.saved_props:
                self.saved_props[prop] = rgetattr(bpy.context, prop)
            rsetattr(bpy.context, prop, value)

        self.report({'INFO'}, 'Baking probe %s' % probe.name)
        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)

class ReflectionProbe(HubsComponent):
    _definition = {
        'name': 'reflection-probe',
        'display_name': 'Reflection Probe',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'MATERIAL'
    }

    envMapTexture: PointerProperty(
        name="EnvMap",
        description="An equirectangular image to use as the environment map for this probe",
        type=Image
    )

    def draw(self, context, layout, panel):
        row = layout.row()
        row.label(text="Resolution settings, as well as the option to bake all reflection probes at once, can be accessed from the scene settings.",
                  icon='INFO')
        super().draw(context, layout, panel)

        global bake_mode
        bake_msg = "Baking..." if probe_baking and bake_mode == 'ACTIVE' else "Bake"
        bake_op = layout.operator(
            "render.hubs_render_reflection_probe",
            text=bake_msg
        )
        bake_op.bake_mode = 'ACTIVE'

        if not hasattr(bpy.context.scene, "cycles"):
            row = layout.row()
            row.alert = True
            row.label(text="Baking requires Cycles addon to be enabled.",
                      icon='ERROR')

    def gather(self, export_settings, object):
        return {
            "size": object.data.influence_distance,
            "envMapTexture": {
                "__mhc_link_type": "texture",
                "index": io.utils.gather_texture(self.envMapTexture, export_settings)
            }
        }

    @ classmethod
    def draw_global(cls, context, layout, panel):
        panel_type = PanelType(panel.bl_context)
        if len(get_probes()) > 0 and panel_type == PanelType.SCENE:
            row = layout.row()
            col = row.box().column()
            row = col.row()
            row.label(text="Reflection Probes Resolution:")
            row = col.row()
            row.prop(context.scene.hubs_scene_reflection_probe_properties,
                     "resolution", text="")

            props = context.scene.hubs_scene_reflection_probe_properties
            if props.resolution != props.render_resolution:
                row = col.row()
                row.alert = True
                row.label(text="Reflection probe resolution has changed. Bake again to apply the new resolution.",
                          icon='ERROR')

            row = col.row()
            row.prop(context.scene.hubs_scene_reflection_probe_properties, "use_compositor")

            global bake_mode

            row = col.row()
            bake_msg = "Baking..." if probe_baking and bake_mode == 'ALL' else "Bake All"
            bake_op = row.operator(
                "render.hubs_render_reflection_probe",
                text=bake_msg
            )
            bake_op.bake_mode = 'ALL'
            bake_msg = "Baking..." if probe_baking and bake_mode == 'SELECTED' else "Bake Selected"
            bake_op = row.operator(
                "render.hubs_render_reflection_probe",
                text=bake_msg
            )
            bake_op.bake_mode = 'SELECTED'

            if not hasattr(bpy.context.scene, "cycles"):
                row = col.row()
                row.alert = True
                row.label(text="Baking requires Cycles addon to be enabled.",
                          icon='ERROR')

    @ classmethod
    def poll(cls, context, panel_type):
        return context.object.type == 'LIGHT_PROBE'

    @ staticmethod
    def register():
        bpy.utils.register_class(BakeProbeOperator)
        bpy.utils.register_class(ReflectionProbeSceneProps)
        bpy.types.Scene.hubs_scene_reflection_probe_properties = PointerProperty(
            type=ReflectionProbeSceneProps)

    @ staticmethod
    def unregister():
        bpy.utils.unregister_class(BakeProbeOperator)
        bpy.utils.unregister_class(ReflectionProbeSceneProps)
        del bpy.types.Scene.hubs_scene_reflection_probe_properties
