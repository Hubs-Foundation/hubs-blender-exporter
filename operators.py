import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy.types import Operator
from . import components
from functools import reduce
import math

class AddHubsComponent(Operator):
    bl_idname = "wm.add_hubs_component"
    bl_label = "Add Hubs Component"
    bl_property = "component_name"

    object_source: StringProperty(name="object_source")
    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        obj = components.get_object_source(context, self.object_source)

        components.add_component(
            obj,
            self.component_name,
            context.scene.hubs_settings.hubs_config,
            context.scene.hubs_settings.registered_hubs_components
        )

        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        object_source = self.object_source
        hubs_components = bpy.context.scene.hubs_settings.registered_hubs_components

        def sort_by_category(acc, v):
            (component_name, component_class) = v
            category = component_class.definition.get("category", "Misc")
            acc[category] = acc.get(category, [])
            acc[category].append(v)
            return acc

        components_by_category = reduce(sort_by_category, hubs_components.items(), {})
        obj = components.get_object_source(context, object_source)

        def draw(self, context):
            row = self.layout.row()
            for category, cmps in components_by_category.items():
                column = row.column()
                column.label(text=category)
                for (component_name, component_class) in cmps:
                    component_display_name = components.dash_to_title(component_name)
                    if not components.is_object_source_component(object_source, component_class.definition): continue

                    if components.has_component(obj, component_name):
                        column.label(text=component_display_name)
                    else:
                        op = column.operator(AddHubsComponent.bl_idname, text = component_display_name, icon='ADD')
                        op.component_name = component_name
                        op.object_source = object_source

        bpy.context.window_manager.popup_menu(draw)

        return {'RUNNING_MODAL'}

class RemoveHubsComponent(Operator):
    bl_idname = "wm.remove_hubs_component"
    bl_label = "Remove Hubs Component"

    object_source: StringProperty(name="object_source")
    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return
        obj = components.get_object_source(context, self.object_source)
        components.remove_component(obj, self.component_name)
        context.area.tag_redraw()
        return {'FINISHED'}

class AddHubsComponentItem(Operator):
    bl_idname = "wm.add_hubs_component_item"
    bl_label = "Add a new item"

    path: StringProperty(name="path")

    def execute(self, context):
        parts = self.path.split(".")

        cur_obj = context

        for part in parts:
            try:
                index = int(part)
                cur_obj = cur_obj[index]
            except:
                cur_obj = getattr(cur_obj, part)

        cur_obj.add()

        context.area.tag_redraw()

        return{'FINISHED'}

class CopyHubsComponent(Operator):
    bl_idname = "wm.copy_hubs_component"
    bl_label = "Copy component from active object"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        src_obj = context.active_object
        dest_objs = filter(lambda item: src_obj != item, context.selected_objects)

        hubs_settings = context.scene.hubs_settings
        component_class = hubs_settings.registered_hubs_components[self.component_name]
        component_class_name = component_class.__name__
        component_definition = hubs_settings.hubs_config['components'][self.component_name]

        if components.has_component(src_obj, self.component_name):
            for dest_obj in dest_objs:
                if components.has_component(dest_obj, self.component_name):
                    components.remove_component(dest_obj, self.component_name)

                components.add_component(
                    dest_obj,
                    self.component_name,
                    hubs_settings.hubs_config,
                    hubs_settings.registered_hubs_components
                )

                src_component = getattr(src_obj, component_class_name)
                dest_component = getattr(dest_obj, component_class_name)

                self.copy_type(hubs_settings, src_component, dest_component, component_definition)

        return{'FINISHED'}


    def copy_type(self, hubs_settings, src_obj, dest_obj, type_definition):
        for property_name, property_definition in type_definition['properties'].items():
            self.copy_property(hubs_settings, src_obj, dest_obj, property_name, property_definition)

    def copy_property(self, hubs_settings, src_obj, dest_obj, property_name, property_definition):
        property_type = property_definition['type']

        if property_type == 'collections':
            return

        registered_types = hubs_settings.hubs_config['types']
        is_custom_type = property_type in registered_types

        src_property = getattr(src_obj, property_name)
        dest_property = getattr(dest_obj, property_name)

        if is_custom_type:
            dest_obj[property_name] = self.copy_type(hubs_settings, src_property, dest_property, registered_types[property_type])
        elif property_type == 'array':
            self.copy_array_property(hubs_settings, src_property, dest_property, property_definition)
        else:
            setattr(dest_obj, property_name, src_property)

    def copy_array_property(self, hubs_settings, src_arr, dest_arr, property_definition):
        array_type = property_definition['arrayType']
        registered_types = hubs_settings.hubs_config['types']
        type_definition = registered_types[array_type]

        dest_arr.clear()

        for src_item in src_arr:
            dest_item = dest_arr.add()
            self.copy_type(hubs_settings, src_item, dest_item, type_definition)


class RemoveHubsComponentItem(Operator):
    bl_idname = "wm.remove_hubs_component_item"
    bl_label = "Remove an item"

    path: StringProperty(name="path")

    def execute(self, context):
        parts = self.path.split(".")

        index = int(parts.pop())

        cur_obj = context

        for part in parts:
            try:
                cur_index = int(part)
                cur_obj = cur_obj[cur_index]
            except:
                cur_obj = getattr(cur_obj, part)

        cur_obj.remove(index)

        context.area.tag_redraw()

        return{'FINISHED'}

class ReloadHubsConfig(Operator):
    bl_idname = "wm.reload_hubs_config"
    bl_label = "Reload Hubs Config"

    def execute(self, context):
        context.scene.hubs_settings.reload_config()
        context.area.tag_redraw()
        return {'FINISHED'}

class ResetHubsComponentNames(Operator):
    bl_idname = "wm.reset_hubs_component_names"
    bl_label = "Reset Selected Hubs Component Names and Ids"

    def execute(self, context):
        for obj in context.selected_objects:
            if components.has_component(obj, "kit-piece"):
                kit_piece = obj.hubs_component_kit_piece
                kit_piece.name = obj.name
                kit_piece.id = obj.name

            if components.has_component(obj, "kit-alt-materials"):
                alt_materials = obj.hubs_component_kit_alt_materials
                alt_materials.name = obj.name
                alt_materials.id = obj.name

        return {'FINISHED'}


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

        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)

        probe_baking = True
        self.probe = context.object

        self.camera_data = bpy.data.cameras.new(name='Temp EnvMap Camera')
        camera_object = bpy.data.objects.new('Temp EnvMap Camera', self.camera_data)
        bpy.context.scene.collection.objects.link(camera_object)

        return _render_probe(self.probe, self.camera_data, camera_object)

    def modal(self, context, event):
        global probe_baking

        # print("ev: %s" % event.type)
        if event.type == 'TIMER' and (self.cancelled or self.done):
            bpy.app.handlers.render_post.remove(self.render_post)
            bpy.app.handlers.render_cancel.remove(self.render_cancelled)
            context.window_manager.event_timer_remove(self._timer)

            bpy.data.cameras.remove(self.camera_data)

            probe_baking = False

            if self.cancelled: return {"CANCELLED"}

            image_name = "generated_cubemap-%s" % self.probe.name
            img = bpy.data.images.get(image_name)
            if not img:
                img = bpy.data.images.load(filepath = bpy.context.scene.render.filepath)
                img.name = image_name
            else:
                img.reload()

            self.probe.hubs_component_reflection_probe['envMapTexture'] = img

            return {"FINISHED"}


        return {"PASS_THROUGH"}


def _render_probe(probe, camera_data, camera_object):
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
        (x, y) = resolutions[probe.hubs_component_reflection_probe.get('resolution', 1)]
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

def register():
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)
    bpy.utils.register_class(CopyHubsComponent)
    bpy.utils.register_class(AddHubsComponentItem)
    bpy.utils.register_class(RemoveHubsComponentItem)
    bpy.utils.register_class(ReloadHubsConfig)
    bpy.utils.register_class(ResetHubsComponentNames)
    bpy.utils.register_class(BakeProbeOperator)

def unregister():
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
    bpy.utils.unregister_class(CopyHubsComponent)
    bpy.utils.unregister_class(AddHubsComponentItem)
    bpy.utils.unregister_class(RemoveHubsComponentItem)
    bpy.utils.unregister_class(ReloadHubsConfig)
    bpy.utils.unregister_class(ResetHubsComponentNames)
    bpy.utils.unregister_class(BakeProbeOperator)
