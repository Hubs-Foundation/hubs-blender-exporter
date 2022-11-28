import bpy
from bpy.props import PointerProperty, EnumProperty, StringProperty, BoolProperty, CollectionProperty
from bpy.types import Image, PropertyGroup, Operator

from ...components.utils import is_gpu_available

from ...preferences import get_addon_pref

from ..components_registry import get_components_registry
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ... import io
from ...utils import rgetattr, rsetattr
from ..utils import redraw_component_ui, is_linked
import math
import os


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


def get_probes(all_objects=False, include_locked=False, include_linked=False):
    probes = []
    objects = bpy.data.objects if all_objects else bpy.context.view_layer.objects
    for ob in objects:
        component_list = ob.hubs_component_list

        registered_hubs_components = get_components_registry()

        if component_list.items:
            for component_item in component_list.items:
                component_name = component_item.name
                if component_name in registered_hubs_components:
                    if component_name == 'reflection-probe':
                        probe_component = ob.hubs_component_reflection_probe
                        if is_linked(ob) and not include_linked:
                            continue
                        if probe_component.locked and not include_locked:
                            continue
                        probes.append(ob)

    return probes


def get_probe_image_path(probe):
    return f"{bpy.app.tempdir}/{probe.name}.hdr"


def update_image_editors(old_img, img):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                if area.spaces.active.image == old_img:
                    area.spaces.active.image = img


def import_menu_draw(self, context):
    self.layout.operator("image.hubs_import_reflection_probe_envmaps",
                         text="Import Reflection Probe EnvMaps")


def export_menu_draw(self, context):
    self.layout.operator("image.hubs_export_reflection_probe_envmaps",
                         text="Export Reflection Probe EnvMaps")


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


class BakeProbeOperator(Operator):
    bl_idname = "render.hubs_render_reflection_probe"
    bl_label = "Render Hubs Reflection Probe"

    _timer = None
    done = False
    rendering = False
    cancelled = False
    probes = []
    probe_index = 0
    probe_is_setup = False

    bake_mode: EnumProperty(
        name="bake_mode",
        items=[('ACTIVE', 'Bake Active', 'Bake Active'),
               ('SELECTED', 'Bake Selected', 'Bake Selected'),
               ('ALL', 'Bake All', 'Bake All')],
        default='ACTIVE')

    disabled_message = "Can't bake linked reflection probes.  Please make it local first"

    @ classmethod
    def description(cls, context, properties):
        if properties.bake_mode == 'ACTIVE':
            description_text = "Generate a 360 equirectangular HDR environment map of the current area in the scene"
            if bpy.app.version < (3, 0, 0) and is_linked(context.active_object):
                description_text += f"\nDisabled: {cls.disabled_message}"
        elif properties.bake_mode == 'SELECTED':
            description_text = "Bake the selected unlocked/local reflection probes"
        else:
            description_text = "Bake all the unlocked/local reflection probes in the current view layer"

        return description_text

    @ classmethod
    def poll(cls, context):
        if hasattr(context, 'bake_active_probe') and is_linked(context.active_object):
            if bpy.app.version >= (3, 0, 0):
                cls.poll_message_set(f"{cls.disabled_message}.")
            return False

        return not probe_baking and hasattr(bpy.context.scene, "cycles")

    def render_post(self, scene, depsgraph):
        print("Finished render")

        self.rendering = False
        self.probe_is_setup = False

        if self.probe_index == 0:
            self.done = True
        else:
            self.probe_index -= 1

    def render_cancelled(self, scene, depsgraph):
        print("Render canceled")
        self.cancelled = True

    def execute(self, context):
        modes = {
            'ACTIVE': lambda: [context.active_object],
            'SELECTED': lambda: [ob for ob in get_probes() if ob in context.selected_objects],
            'ALL': lambda: get_probes(),
        }
        self.probes = modes[self.bake_mode]()

        if self.bake_mode == 'SELECTED' and len(self.probes) == 0:
            def draw(self, context):
                self.layout.label(
                    text="No probes selected to bake or the selected probes are locked/linked. Please select some unlocked/local probes first.")
            bpy.context.window_manager.popup_menu(
                draw, title="No unlocked/local probes selected", icon='ERROR')
            return {'CANCELLED'}
        if self.bake_mode == 'ALL' and len(self.probes) == 0:
            def draw(self, context):
                self.layout.label(
                    text="No unlocked/local probes to bake. Please unlock/make local the desired probes first.")
            bpy.context.window_manager.popup_menu(
                draw, title="No unlocked/local probes", icon='ERROR')
            return {'CANCELLED'}
        if self.bake_mode == 'ACTIVE' and is_linked(self.probes[0]):
            # This isn't likely to ever happen, but just in case....
            def draw(self, context):
                self.layout.label(
                    text="The active probe is linked. Please make it local first.")
            bpy.context.window_manager.popup_menu(
                draw, title="Active probe linked", icon='ERROR')
            return {'CANCELLED'}
        if self.bake_mode == 'ACTIVE' and self.probes[0].hubs_component_reflection_probe.locked:
            # This isn't likely to ever happen, but just in case....
            def draw(self, context):
                self.layout.label(
                    text="The active probe is locked. Please unlock it first.")
            bpy.context.window_manager.popup_menu(
                draw, title="Active probe locked", icon='ERROR')
            return {'CANCELLED'}

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

        self.saved_props = {}
        self.preferences_is_dirty_state = bpy.context.preferences.is_dirty
        self.cancelled = False
        self.done = False
        self.rendering = False
        self.probe_is_setup = False
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
                self.probe_is_setup = False

                if self.cancelled:
                    for probe in self.probes:
                        img_path = get_probe_image_path(probe)
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    self.report(
                        {'WARNING'}, 'Reflection probe baking cancelled')
                    return {"CANCELLED"}

                for probe in self.probes:
                    probe_component = probe.hubs_component_reflection_probe
                    old_img = probe_component.envMapTexture
                    image_name = f"generated_cubemap-{probe.name}"
                    # Store the old image's name in case of name juggling.
                    old_img_name = old_img.name if old_img else ""

                    conflicting_img = None
                    for img in bpy.data.images:
                        if img.name == image_name and not is_linked(img):
                            conflicting_img = img
                            break

                    if conflicting_img and conflicting_img != old_img:
                        # Rename the conflicting image to help avoid problems caused by Blender's name juggling and allow name juggled images to be more easily found.
                        conflicting_img.name = f"{conflicting_img.name}-old"

                    img_path = get_probe_image_path(probe)
                    img = bpy.data.images.load(filepath=img_path)
                    img.name = image_name
                    if old_img:
                        if image_name == old_img_name and not is_linked(old_img):
                            old_img.user_remap(img)
                            bpy.data.images.remove(old_img)
                        else:
                            update_image_editors(old_img, img)

                    probe_component['envMapTexture'] = img

                    # Pack image and update filepaths so that it displays/unpacks nicely for the user.
                    # Note: updating the filepaths prints an error to the terminal, but otherwise seems to work fine.
                    img.pack()
                    new_filepath = f"//{image_name}.hdr"
                    img.packed_files[0].filepath = new_filepath
                    img.filepath_raw = new_filepath
                    img.filepath = new_filepath
                    if os.path.exists(img_path):
                        os.remove(img_path)

                props = context.scene.hubs_scene_reflection_probe_properties
                props.render_resolution = props.resolution

                self.report({'INFO'}, 'Reflection probe baking finished')
                return {"FINISHED"}

            elif not self.rendering:
                try:
                    if not self.probe_is_setup:
                        self.setup_probe_render(context)

                    # Rendering can sometimes fail if the old render is still being cleaned up.  Keep trying until it works.
                    # For more details see https://developer.blender.org/T52258
                    if bpy.ops.render.render("INVOKE_DEFAULT", write_still=True) != {'CANCELLED'}:
                        self.rendering = True

                except Exception as e:
                    print(e)
                    self.cancelled = True
                    self.report(
                        {'ERROR'}, 'Reflection probe baking error %s' % e)

        return {"PASS_THROUGH"}

    def restore_render_props(self):
        for prop in self.saved_props:
            rsetattr(bpy.context, prop, self.saved_props[prop])
        bpy.context.preferences.is_dirty = self.preferences_is_dirty_state
        self.preferences_is_dirty_state = None

    def setup_probe_render(self, context):
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
        output_path = get_probe_image_path(probe)
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
        self.probe_is_setup = True


class OpenReflectionProbeEnvMap(Operator):
    bl_idname = "image.hubs_open_reflection_probe_envmap"
    bl_label = "Open EnvMap"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")
    files: CollectionProperty(type=PropertyGroup)
    filter_folder: BoolProperty(default=True, options={"HIDDEN"})
    filter_image: BoolProperty(default=True, options={"HIDDEN"})

    relative_path: BoolProperty(
        name="Relative Path", description="Select the file relative to the blend file", default=True)

    disabled_message = "Can't open/assign environment maps to linked reflection probes.  Please make it local first"

    @ classmethod
    def description(cls, context, properties):
        description_text = "Load an external image to be used as this probe's environment map"
        if bpy.app.version < (3, 0, 0) and is_linked(context.active_object):
            description_text += f"\nDisabled: {cls.disabled_message}"

        return description_text

    @ classmethod
    def poll(cls, context):
        if is_linked(context.active_object):
            if bpy.app.version >= (3, 0, 0):
                cls.poll_message_set(f"{cls.disabled_message}.")
            return False

        return True

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "relative_path")

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)

        if not self.files[0].name:
            self.report({'INFO'}, "Open EnvMap cancelled.  No image selected.")
            return {'CANCELLED'}

        probe_component = context.active_object.hubs_component_reflection_probe
        old_img = probe_component['envMapTexture']

        # Load/Reload the first image and assign it to the reflection probe, then load the rest of the images if they're not already loaded.  This mimics Blender's default open files behavior.
        primary_filepath = os.path.join(dirname, self.files[0].name)
        primary_img = bpy.data.images.load(
            filepath=primary_filepath, check_existing=True)
        primary_img.reload()
        probe_component['envMapTexture'] = primary_img

        for f in self.files[1:]:
            img = bpy.data.images.load(filepath=os.path.join(
                dirname, f.name), check_existing=True)

        update_image_editors(old_img, primary_img)
        redraw_component_ui(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportReflectionProbeEnvMaps(Operator):
    bl_idname = "image.hubs_import_reflection_probe_envmaps"
    bl_label = "Import EnvMaps"
    bl_description = "Batch open environment maps and assign them to their corresponding reflection probes"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")
    files: CollectionProperty(type=PropertyGroup)
    filter_folder: BoolProperty(default=True, options={"HIDDEN"})
    filter_image: BoolProperty(default=True, options={"HIDDEN"})

    relative_path: BoolProperty(
        name="Relative Path", description="Select the file relative to the blend file", default=True)
    overwrite_images: BoolProperty(
        name="Overwrite Probe Images", description="Overwrite/Remove the current images of the reflection probes being imported to", default=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "relative_path")
        layout.prop(self, "overwrite_images")
        layout.separator()
        info_col = layout.column()
        info_col.scale_y = 0.7
        info_col.label(text="Load the selected images", icon='INFO')
        info_col.label(text="into the matching probes.", icon='BLANK1')
        info_col.label(text="Images must start with the", icon='BLANK1')
        info_col.label(text="respective probe's name", icon='BLANK1')
        info_col.label(text="formatted like this:", icon='BLANK1')
        info_col.label(text="\"<Probe Name> - EnvMap\"", icon='BLANK1')

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)

        if not self.files[0].name:
            self.report(
                {'INFO'}, "Import EnvMaps cancelled.  No images selected.")
            return {'CANCELLED'}

        num_imported = 0
        num_failed = 0
        probes = get_probes(all_objects=True)
        for f in self.files:
            imported_file = False
            for probe in probes:
                if f.name.startswith(f"{probe.name} - EnvMap"):
                    probe_component = probe.hubs_component_reflection_probe
                    old_img = probe_component['envMapTexture']

                    img = bpy.data.images.load(
                        filepath=os.path.join(dirname, f.name))
                    probe_component['envMapTexture'] = img

                    if old_img:
                        if self.overwrite_images:
                            if old_img.name == f.name:
                                img.name = f.name

                            old_img.user_remap(img)

                            if not is_linked(old_img):
                                bpy.data.images.remove(old_img)

                        else:
                            update_image_editors(old_img, img)

                    imported_file = True
                    num_imported += 1
                    self.report(
                        {'INFO'}, f"Imported {f.name} to probe {probe.name}")

            if not imported_file:
                num_failed += 1
                self.report(
                    {'WARNING'}, f"Warning: Couldn't import {f.name}.  The corresponding probe either doesn't exist or is locked/linked.")

        if num_failed:
            final_report_message = f"Warning: {num_failed} environment maps failed to import. {num_imported} environment maps imported to probes"
        else:
            final_report_message = f"{num_imported} environment maps imported to probes"
        self.report({'INFO'}, final_report_message)

        redraw_component_ui(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportReflectionProbeEnvMaps(Operator):
    bl_idname = "image.hubs_export_reflection_probe_envmaps"
    bl_label = "Export EnvMaps"
    bl_description = "Batch save out the current environment maps from reflection probes"

    directory: StringProperty(subtype="DIR_PATH")
    filter_folder: BoolProperty(default=True, options={"HIDDEN"})
    filter_image: BoolProperty(default=True, options={"HIDDEN"})

    batch_type: EnumProperty(
        name="Batch Type",
        description="Choose which probes to export",
        items=(
            ('ALL', "All Probes",
             "Export the environment maps from all probes in the current view layer"),
            ('SELECTED', "Selected Probes",
             "Export the environment maps from the selected probes"),
        ),
        default='ALL',
    )

    include_locked: BoolProperty(
        name="Include Locked", description="Include environment maps from locked probes", default=False)

    naming_scheme: StringProperty(
        name="Output Naming Scheme",
        description="How exported files will be named",
        default="<Probe Name> - EnvMap.hdr"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Export EnvMaps for:")
        layout.prop(self, "batch_type", expand=True)
        layout.prop(self, "include_locked")
        layout.separator()
        row = layout.row()
        row.prop(self, "naming_scheme", text="To")
        row.enabled = False

    def execute(self, context):
        if self.batch_type == 'SELECTED':
            probes = [ob for ob in get_probes(
                include_locked=self.include_locked) if ob in context.selected_objects]
        else:
            probes = get_probes(include_locked=self.include_locked)

        if not probes:
            self.report(
                {'WARNING'}, "Export EnvMaps cancelled.  No local probes matching the criteria were found.")
            return {'CANCELLED'}

        num_exported = 0
        for probe in probes:
            envMapTexture = probe.hubs_component_reflection_probe.envMapTexture
            if envMapTexture:
                export_path = f"{self.directory}/{probe.name} - EnvMap.hdr"
                orig_filepath_raw = envMapTexture.filepath_raw
                envMapTexture.filepath_raw = export_path
                envMapTexture.save()
                envMapTexture.filepath_raw = orig_filepath_raw
                self.report(
                    {'INFO'}, f"Exported environment map for probe {probe.name}")
                num_exported += 1
            else:
                self.report(
                    {'WARNING'}, f"Reflection probe {probe.name} doesn't have an environment map to export")
        self.report(
            {'INFO'}, f"Exported {num_exported} environment maps to {self.directory}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SelectMismatchedReflectionProbes(Operator):
    bl_idname = "wm.hubs_select_mismatched_reflection_probes"
    bl_label = "Select Mismatched Reflection Probes"
    bl_description = "Select reflection probes in the current view layer with environment maps that don't match the global resolution"
    bl_options = {'REGISTER', 'UNDO'}

    select_all: BoolProperty(default=False)
    mismatched_probe_indexes: StringProperty()

    def execute(self, context):
        if self.select_all:
            bpy.ops.object.select_all(action='DESELECT')
            probes = get_probes(include_locked=True, include_linked=True)
            for index in map(int, self.mismatched_probe_indexes.split(',')):
                probe = probes[index]
                probe.select_set(True)
            context.view_layer.objects.active = None
            return {'FINISHED'}

        probe = context.probe

        # Check if the probe can be selected.
        probe.select_set(True)
        if not probe.select_get():
            self.report({'INFO'}, f"Couldn't select probe {probe.name_full}")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        probe.select_set(True)
        context.view_layer.objects.active = probe
        return {'FINISHED'}

    def invoke(self, context, event):
        probes = get_probes(include_locked=True, include_linked=True)

        def draw(self, context):
            layout = self.layout
            layout.label(text="Select Mismatched Probes")
            layout.separator()

            props = context.scene.hubs_scene_reflection_probe_properties
            mismatched_probe_indexes = []
            mismatched_probes = []
            for i, probe in enumerate(probes):
                envmap = probe.hubs_component_reflection_probe.envMapTexture
                if envmap:
                    envmap_resolution = f"{envmap.size[0]}x{envmap.size[1]}"
                    if envmap_resolution != props.resolution:
                        mismatched_probe_indexes.append(i)
                        mismatched_probes.append(probe)

            is_selected = (context.selected_objects ==
                           mismatched_probes and not context.active_object)
            icon = 'RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF'
            op = layout.operator(
                SelectMismatchedReflectionProbes.bl_idname, text="Select All", icon=icon)
            op.select_all = True
            op.mismatched_probe_indexes = ','.join(
                map(str, mismatched_probe_indexes))

            layout.separator()

            for probe in mismatched_probes:
                is_selected = (probe == context.active_object and probe in context.selected_objects and len(
                    context.selected_objects) == 1)
                icon = 'RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF'
                row = layout.row()
                row.context_pointer_set("probe", probe)
                op = row.operator(
                    SelectMismatchedReflectionProbes.bl_idname, text=probe.name_full, icon=icon)
                op.select_all = False
                op.mismatched_probe_indexes = ''

        bpy.context.window_manager.popup_menu(draw)
        return {'RUNNING_MODAL'}


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

    locked: BoolProperty(
        name="Probe Lock", description="Toggle whether new environment maps can be assigned/baked to this reflection probe", default=False)

    def draw(self, context, layout, panel):
        row = layout.row()
        row.alignment = 'LEFT'
        icon = 'LOCKED' if self.locked else 'UNLOCKED'
        row.prop(self, "locked", text='', icon=icon, toggle=True)

        row = layout.row()
        row.label(text="Resolution settings, as well as the option to bake all reflection probes at once, can be accessed from the scene settings.",
                  icon='INFO')
        row = layout.row(align=True)
        row.prop(self, "envMapTexture")
        row.operator("image.hubs_open_reflection_probe_envmap",
                     text='', icon='FILE_FOLDER')

        if self.locked:
            row.enabled = False

        envmap = self.envMapTexture
        if envmap:
            envmap_resolution = f"{envmap.size[0]}x{envmap.size[1]}"
            props = context.scene.hubs_scene_reflection_probe_properties
            if not envmap.has_data:
                row = layout.row()
                row.alert = True
                row.label(text="Can't load image.",
                          icon='ERROR')
            elif envmap_resolution != props.resolution:
                row = layout.row()
                row.alert = True
                row.label(text=f"{envmap_resolution} EnvMap doesn't match the scene probe resolution.",
                          icon='ERROR')

        global bake_mode
        row = layout.row()
        row.context_pointer_set("bake_active_probe", None)
        bake_msg = "Baking..." if probe_baking and bake_mode == 'ACTIVE' else "Bake"
        bake_op = row.operator(
            "render.hubs_render_reflection_probe",
            text=bake_msg
        )
        bake_op.bake_mode = 'ACTIVE'

        if self.locked:
            row.enabled = False

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
        probes = get_probes(include_locked=True, include_linked=True)
        if len(probes) > 0 and panel_type == PanelType.SCENE:
            row = layout.row()
            col = row.box().column()
            row = col.row()
            row.label(text="Reflection Probes Resolution:")
            row = col.row()
            row.prop(context.scene.hubs_scene_reflection_probe_properties,
                     "resolution", text="")

            props = context.scene.hubs_scene_reflection_probe_properties
            mismatched_probes = 0
            for probe in probes:
                envmap = probe.hubs_component_reflection_probe.envMapTexture
                if envmap:
                    envmap_resolution = f"{envmap.size[0]}x{envmap.size[1]}"
                    if envmap_resolution != props.resolution:
                        mismatched_probes += 1

            if mismatched_probes:
                if props.resolution != props.render_resolution:
                    row = col.row()
                    row.alert = True
                    row.label(text="Reflection probe resolution has changed. Bake again to apply the new resolution.",
                              icon='ERROR')
                row = col.row()
                row.alert = True
                row.label(text=f"{mismatched_probes} probes don't match the current resolution.",
                          icon='ERROR')
                row.operator("wm.hubs_select_mismatched_reflection_probes",
                             text="", icon='RESTRICT_SELECT_OFF')

            row = col.row()
            row.prop(
                context.scene.hubs_scene_reflection_probe_properties, "use_compositor")

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
        bpy.utils.register_class(OpenReflectionProbeEnvMap)
        bpy.utils.register_class(ImportReflectionProbeEnvMaps)
        bpy.utils.register_class(ExportReflectionProbeEnvMaps)
        bpy.utils.register_class(SelectMismatchedReflectionProbes)
        bpy.types.Scene.hubs_scene_reflection_probe_properties = PointerProperty(
            type=ReflectionProbeSceneProps)
        bpy.types.TOPBAR_MT_file_import.append(import_menu_draw)
        bpy.types.TOPBAR_MT_file_export.append(export_menu_draw)

    @ staticmethod
    def unregister():
        bpy.utils.unregister_class(BakeProbeOperator)
        bpy.utils.unregister_class(ReflectionProbeSceneProps)
        bpy.utils.unregister_class(OpenReflectionProbeEnvMap)
        bpy.utils.unregister_class(ImportReflectionProbeEnvMaps)
        bpy.utils.unregister_class(ExportReflectionProbeEnvMaps)
        bpy.utils.unregister_class(SelectMismatchedReflectionProbes)
        del bpy.types.Scene.hubs_scene_reflection_probe_properties
        bpy.types.TOPBAR_MT_file_import.remove(import_menu_draw)
        bpy.types.TOPBAR_MT_file_export.remove(export_menu_draw)
