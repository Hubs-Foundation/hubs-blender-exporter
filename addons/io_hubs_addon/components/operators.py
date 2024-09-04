import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty, FloatProperty
from bpy.types import Operator, PropertyGroup
from functools import reduce

from .types import PanelType, MigrationType
from .utils import get_object_source, has_component, add_component, remove_component, wrap_text, display_wrapped_text, is_dep_required, update_image_editors
from .components_registry import get_components_registry, get_component_by_name
from ..preferences import get_addon_pref
from .handlers import migrate_components
from .gizmos import update_gizmos
from .utils import is_linked, redraw_component_ui
from ..icons import get_hubs_icons
from .consts import LIGHTMAP_LAYER_NAME, LIGHTMAP_UV_ISLAND_MARGIN
import os


class AddHubsComponent(Operator):
    bl_idname = "wm.add_hubs_component"
    bl_label = "Add Hubs Component"
    bl_property = "component_name"
    bl_options = {'REGISTER', 'UNDO'}

    panel_type: StringProperty(name="panel_type")
    component_name: StringProperty(name="component_name")

    @classmethod
    def poll(cls, context):
        if hasattr(context, "panel"):
            panel = getattr(context, 'panel')
            panel_type = PanelType(panel.bl_context)
            if panel_type == PanelType.SCENE:
                if is_linked(context.scene):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot add components to linked scenes")
                    return False
            elif panel_type == PanelType.OBJECT:
                if is_linked(context.active_object):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot add components to linked objects")
                    return False
            elif panel_type == PanelType.MATERIAL:
                if is_linked(context.active_object.active_material):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot add components to linked materials")
                    return False
            elif panel_type == PanelType.BONE:
                if is_linked(context.active_bone):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot add components to linked bones")
                    return False

        return True

    def execute(self, context):
        if self.component_name == '':
            return

        obj = get_object_source(context, self.panel_type)
        add_component(obj, self.component_name)

        # Redraw panel and trigger depsgraph update
        context.area.tag_redraw()
        context.window_manager.update_tag()
        return {'FINISHED'}

    def invoke(self, context, event):
        panel_type = self.panel_type

        # Filter components that are not targeted to this object type or their poll method call returns False
        def filter_source_type(cmp):
            (_, component_class) = cmp
            host = get_object_source(context, panel_type)
            return not component_class.is_dep_only() and PanelType(panel_type) in component_class.get_panel_type() and component_class.poll(PanelType(panel_type), host, ob=context.object)

        components_registry = get_components_registry()
        hubs_icons = get_hubs_icons()
        filtered_components = dict(
            filter(filter_source_type, components_registry.items()))

        def sort_by_category(acc, cmp):
            (_, component_class) = cmp
            category = component_class.get_category_name()
            acc[category] = acc.get(category, [])
            acc[category].append(cmp)
            return acc

        components_by_category = reduce(
            sort_by_category, filtered_components.items(), {})
        obj = get_object_source(context, panel_type)

        def draw(self, context):
            added_comps = 0
            row_length = get_addon_pref(context).row_length
            row = self.layout.row()

            column_sorted_category_components = {}
            row_max_cmp_len = {}

            # sort components categories alphabetically and into columns and record the length of
            # the longest category per row.  Number of columns == row_length
            for cat_idx, category_cmps in enumerate(sorted(components_by_category.items())):
                # add a tuple of the categories and components to the proper column index based on row length
                try:
                    column_sorted_category_components[cat_idx % row_length].append(
                        category_cmps)
                except KeyError:
                    column_sorted_category_components[cat_idx % row_length] = [
                        category_cmps]
                # if the row length is zero, then just add a column for each category
                except ZeroDivisionError:
                    column_sorted_category_components[cat_idx] = [
                        category_cmps]

                # get the number of components in this category
                cmp_len = len(category_cmps[1])

                # get which row we're on
                try:
                    row_idx = len(
                        column_sorted_category_components[cat_idx % row_length]) - 1
                except ZeroDivisionError:
                    row_idx = len(
                        column_sorted_category_components[cat_idx]) - 1

                # update the maximum number of components in a category for this row
                try:
                    row_max_cmp_len[row_idx] = cmp_len if cmp_len > row_max_cmp_len[row_idx] else row_max_cmp_len[row_idx]
                except KeyError:
                    row_max_cmp_len[row_idx] = cmp_len

            # loop through the columns
            for column_idx, category_cmps in column_sorted_category_components.items():
                column = row.column()

                # loop through and add the categories for this column
                for cat_idx, (category, cmps) in enumerate(category_cmps):
                    column.label(text=category)
                    column.separator()

                    # loop through and add the components in this category
                    cmp_idx = 0
                    for (component_name, component_class) in cmps:
                        if component_class.is_dep_only():
                            continue

                        cmp_idx += 1
                        component_name = component_class.get_name()
                        component_display_name = component_class.get_display_name()

                        op = None
                        if component_class.get_icon() is not None:
                            icon = component_class.get_icon()
                            if icon.find('.') != -1:
                                if has_component(obj, component_name):
                                    op = column.label(
                                        text=component_display_name, icon_value=hubs_icons[icon].icon_id)
                                else:
                                    op = column.operator(
                                        AddHubsComponent.bl_idname, text=component_display_name,
                                        icon_value=hubs_icons[icon].icon_id)
                                    op.component_name = component_name
                                    op.panel_type = panel_type
                            else:
                                if has_component(obj, component_name):
                                    op = column.label(
                                        text=component_display_name, icon=icon)
                                else:
                                    op = column.operator(
                                        AddHubsComponent.bl_idname, text=component_display_name, icon=icon)
                                    op.component_name = component_name
                                    op.panel_type = panel_type
                        else:
                            if has_component(obj, component_name):
                                op = column.label(text=component_display_name)
                            else:
                                op = column.operator(
                                    AddHubsComponent.bl_idname, text=component_display_name, icon='ADD')
                                op.component_name = component_name
                                op.panel_type = panel_type

                        added_comps += 1

                    # add blank space padding to category so it will take up the same space as the category with the most components in that row (keeps rows aligned)
                    while cmp_idx < row_max_cmp_len[cat_idx] and cat_idx + 1 < len(category_cmps):
                        column.label(text="")
                        cmp_idx += 1

                    # add blank space between rows, but not after final row
                    if cat_idx + 1 < len(column_sorted_category_components[column_idx]):
                        column.label(text="")

            if added_comps == 0:
                column = row.column()
                column.label(
                    text="No components available for this object type")

        bpy.context.window_manager.popup_menu(draw)

        return {'FINISHED'}


class RemoveHubsComponent(Operator):
    bl_idname = "wm.remove_hubs_component"
    bl_label = "Remove Hubs Component"
    bl_options = {'REGISTER', 'UNDO'}

    panel_type: StringProperty(name="panel_type")
    component_name: StringProperty(name="component_name")

    @classmethod
    def poll(cls, context):
        if hasattr(context, "panel"):
            panel = getattr(context, 'panel')
            panel_type = PanelType(panel.bl_context)
            if panel_type == PanelType.SCENE:
                if is_linked(context.scene):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot remove components from linked scenes")
                    return False
            elif panel_type == PanelType.OBJECT:
                if is_linked(context.active_object):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot remove components from linked objects")
                    return False
            elif panel_type == PanelType.MATERIAL:
                if is_linked(context.active_object.active_material):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot remove components from linked materials")
                    return False
            elif panel_type == PanelType.BONE:
                if is_linked(context.active_bone):
                    if bpy.app.version >= (3, 0, 0):
                        cls.poll_message_set(
                            "Cannot add components to linked bones")
                    return False

        return True

    def execute(self, context):
        if self.component_name == '':
            return
        obj = get_object_source(context, self.panel_type)
        remove_component(obj, self.component_name)

        # Redraw panel and trigger depsgraph update
        context.area.tag_redraw()
        context.window_manager.update_tag()
        return {'FINISHED'}


class MigrateHubsComponents(Operator):
    bl_idname = "wm.migrate_hubs_components"
    bl_label = "Migrate Hubs Components"
    bl_description = "Loops through all objects/components and attempts to migrate them to the current version based on their internal version"
    bl_options = {'REGISTER', 'UNDO'}

    # For some reason using a default value with this property doesn't work properly, so the value must be manually specified each time.
    is_registration: BoolProperty(options={'HIDDEN'})

    def execute(self, context):
        if self.is_registration:
            migrate_components(MigrationType.REGISTRATION,
                               do_beta_versioning=True)
        else:
            migrate_components(MigrationType.LOCAL, do_beta_versioning=True)

        return {'FINISHED'}


class UpdateHubsGizmos(Operator):
    bl_idname = "wm.update_hubs_gizmos"
    bl_label = "Refresh Hubs Gizmos"
    bl_description = "Force a re-evaluation of all objects/components and update their gizmos"

    def execute(self, context):
        update_gizmos()
        return {'FINISHED'}


class ViewLastReport(Operator):
    bl_idname = "wm.hubs_view_last_report"
    bl_label = "View Last Hubs Report"
    bl_description = "Show the latest Hubs report in the Hubs Report Viewer"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return wm.hubs_report_last_title and wm.hubs_report_last_report_string

    def execute(self, context):
        wm = context.window_manager
        title = wm.hubs_report_last_title
        report_string = wm.hubs_report_last_report_string
        bpy.ops.wm.hubs_report_viewer(
            'INVOKE_DEFAULT', title=title, report_string=report_string)
        return {'FINISHED'}


class ViewReportInInfoEditor(Operator):
    bl_idname = "wm.hubs_view_report_in_info_editor"
    bl_label = "View Report in the Info Editor"
    bl_description = "Save the Hubs report to the Info Editor and open it for viewing"

    title: StringProperty(default="")
    report_string: StringProperty()

    def highlight_info_report(self):
        context_override = bpy.context.copy()
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'INFO':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            context_override['area'] = area
                            context_override['region'] = region
                            # Find and select the last info message for each Info editor.
                            index = 0
                            while bpy.ops.info.select_pick(
                                    context_override, report_index=index, extend=False) != {'CANCELLED'}:
                                index += 1
                            bpy.ops.info.select_pick(
                                context_override, report_index=index, extend=False)

    def execute(self, context):
        messages = split_and_prefix_report_messages(self.report_string)
        info_report_string = '\n'.join(
            [message.replace('\n', '  ') for message in messages])
        self.report(
            {'INFO'}, f"Hubs {self.title}\n{info_report_string}\nEnd of Hubs {self.title}")
        bpy.ops.screen.info_log_show()
        bpy.app.timers.register(self.highlight_info_report)
        return {'FINISHED'}


class ReportScroller(Operator):
    bl_idname = "wm.hubs_report_scroller"
    bl_label = "Hubs Report Scroller"

    increment: IntProperty()
    maximum: IntProperty()

    @classmethod
    def description(self, context, properties):
        if properties.increment == -1:
            return "Scroll up one line.\nShift+Click to scroll to the beginning"
        if properties.increment == 1:
            return "Scroll down one line.\nShift+Click to scroll to the end"

    def invoke(self, context, event):
        wm = context.window_manager

        if event.shift:  # Jump to beginning/end
            if self.increment == -1:
                wm.hubs_report_scroll_index = 0
                wm.hubs_report_scroll_percentage = 0
                return {'FINISHED'}
            else:  # 1
                wm.hubs_report_scroll_index = self.maximum
                wm.hubs_report_scroll_percentage = 100
                return {'FINISHED'}

        else:  # Increment/Decrement
            current_scroll_index = wm.hubs_report_scroll_index
            if current_scroll_index + self.increment < 0:
                return {'CANCELLED'}
            elif current_scroll_index + self.increment > self.maximum:
                return {'CANCELLED'}
            else:
                wm.hubs_report_scroll_index += self.increment
                current_scroll_index = wm.hubs_report_scroll_index
                wm.hubs_report_scroll_percentage = current_scroll_index * 100 // self.maximum
                return {'FINISHED'}


class ReportViewer(Operator):
    bl_idname = "wm.hubs_report_viewer"
    bl_label = "Hubs Report Viewer"

    title: StringProperty(default="")
    report_string: StringProperty()

    def draw(self, context):
        layout = self.layout

        layout.label(text=self.title)

        row = layout.row()
        column = row.column()
        box = column.box()

        wm = context.window_manager
        report_length = len(self.messages)
        maximum_scrolling = len(self.report_display_blocks) - 1
        start_index = wm.hubs_report_scroll_index
        block_messages = self.report_display_blocks[start_index]

        displayed_lines = 0
        message_column = box.column()
        for message in block_messages:
            display_wrapped_text(message_column, message, heading_icon='INFO')
            displayed_lines += len(message)

        # Add padding to the bottom of the report if needed (accounts for the formatting changes when there are only a few messages in the report).
        while displayed_lines < self.lines_to_show:
            display_wrapped_text(message_column, [""])
            displayed_lines += 1

        scroll_column = row.column()
        scroll_column.enabled = report_length > len(block_messages)

        scroll_up = scroll_column.row()
        scroll_up.enabled = start_index > 0
        op = scroll_up.operator(ReportScroller.bl_idname,
                                text="", icon="TRIA_UP")
        op.increment = -1
        op.maximum = maximum_scrolling

        scroll_down = scroll_column.row()
        scroll_down.enabled = start_index < maximum_scrolling
        op = scroll_down.operator(
            ReportScroller.bl_idname, text="", icon="TRIA_DOWN")
        op.increment = 1
        op.maximum = maximum_scrolling

        total_messages = column.row()
        total_messages.alignment = 'RIGHT'
        total_messages.label(text=f"{report_length} Messages")

        scroll_percentage = column.row()
        scroll_percentage.enabled = False
        scroll_percentage.prop(
            wm, "hubs_report_scroll_percentage", slider=True)

        layout.separator()

        op = layout.operator(ViewReportInInfoEditor.bl_idname)
        op.title = self.title
        op.report_string = self.report_string

    def execute(self, context):
        return {'FINISHED'}

    def init_report_display_blocks(self):
        start_index = 0
        self.report_display_blocks = {}

        final_block = False
        while start_index < len(self.messages) and not final_block:
            block_messages = []
            for message in self.messages[start_index:]:
                wrapped_message = wrap_text(message, max_length=90)
                block_messages.append(wrapped_message)

            last_message = None
            while True:
                if len(block_messages) == 1:
                    break

                if len(block_messages) > self.messages_to_show:
                    last_message = block_messages.pop()
                elif sum([len(message) + 1 for message in block_messages]) - 1 > self.lines_to_show:
                    # The +1 and -1 are used to account for padding lines between messages.
                    last_message = block_messages.pop()
                else:
                    break

            if last_message is None:
                final_block = True

            current_block_lines = sum([len(message)
                                      for message in block_messages])
            needed_padding_lines = self.lines_to_show - current_block_lines

            message_iter = iter(block_messages)
            while needed_padding_lines > 0:
                try:
                    next(message_iter).append("")
                except StopIteration:
                    if len(self.messages) < 4:
                        # Evenly spacing the messages doesn't look good if there are only a few messages in the report, so let any extra padding be added to the end when it's displayed.
                        break

                    message_iter = reversed(block_messages)
                    next(message_iter).append("")

                needed_padding_lines += -1

            self.report_display_blocks[start_index] = block_messages
            start_index += 1

    def invoke(self, context, event):
        wm = context.window_manager
        self.messages = split_and_prefix_report_messages(self.report_string)
        self.lines_to_show = 15
        self.messages_to_show = 5
        wm.hubs_report_scroll_index = 0
        wm.hubs_report_scroll_percentage = 0
        wm.hubs_report_last_title = self.title
        wm.hubs_report_last_report_string = self.report_string
        self.init_report_display_blocks()
        return wm.invoke_props_dialog(self, width=600)


def split_and_prefix_report_messages(report_string):
    return [f"{i + 1:02d}   {message}" for i, message in enumerate(report_string.split("\n\n"))]


class CopyHubsComponent(Operator):
    bl_idname = "wm.copy_hubs_component"
    bl_label = "Copy component from active object"
    bl_options = {'REGISTER', 'UNDO'}

    panel_type: StringProperty(name="panel_type")
    component_name: StringProperty(name="component_name")

    @classmethod
    def poll(cls, context):
        if is_linked(context.scene):
            if bpy.app.version >= (3, 0, 0):
                cls.poll_message_set(
                    "Cannot copy components when in linked scenes")
            return False

        if hasattr(context, "panel"):
            panel = getattr(context, 'panel')
            panel_type = PanelType(panel.bl_context)
            return panel_type != PanelType.SCENE

        return True

    def get_selected_bones(self, context):
        selected_bones = context.selected_pose_bones if context.mode == "POSE" else context.selected_editable_bones
        selected_armatures = [
            sel_ob for sel_ob in context.selected_objects if sel_ob.type == "ARMATURE"]
        selected_hosts = []
        for armature in selected_armatures:
            armature_bones = armature.pose.bones if context.mode == "POSE" else armature.data.edit_bones
            target_armature_bones = armature.data.bones if context.mode == "POSE" else armature.data.edit_bones
            target_bones = [
                bone for bone in armature_bones if bone in selected_bones]
            for target_bone in target_bones:
                selected_hosts.extend(
                    [bone for bone in target_armature_bones if target_bone.name == bone.name])
        return selected_hosts

    def get_selected_hosts(self, context):
        selected_hosts = []
        for host in context.selected_objects:
            if host.type == "ARMATURE" and context.mode != "OBJECT":
                selected_hosts.extend(self.get_selected_bones(context))
            else:
                selected_hosts.append(host)

        return selected_hosts

    def execute(self, context):
        src_host = None
        selected_hosts = []
        if self.panel_type == PanelType.OBJECT.value:
            src_host = context.active_object
            selected_hosts = self.get_selected_hosts(context)
        elif self.panel_type == PanelType.BONE.value:
            src_host = context.active_bone
            selected_hosts = self.get_selected_hosts(context)
        elif self.panel_type == PanelType.MATERIAL.value:
            src_host = context.active_object.active_material
            selected_hosts = [
                ob.active_material for ob in context.selected_objects
                if ob.active_material and ob.active_material is not None and ob.active_material is not src_host]

        component_class = get_component_by_name(self.component_name)
        component_id = component_class.get_id()
        for dest_host in selected_hosts:
            if is_linked(dest_host):
                continue

            if component_class.is_dep_only():
                if not is_dep_required(dest_host, None, self.component_name):
                    continue

            if not has_component(dest_host, self.component_name):
                add_component(dest_host, self.component_name)

            for key, value in src_host[component_id].items():
                dest_host[component_id][key] = value

            deps_names = component_class.get_deps()
            for dep_name in deps_names:
                dep_class = get_component_by_name(dep_name)
                dep_id = dep_class.get_id()
                for key, value in src_host[dep_id].items():
                    dest_host[dep_id][key] = value

        return {'FINISHED'}


class OpenImage(Operator):
    bl_idname = "image.hubs_open_image"
    bl_label = "Open Image"
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty()
    filepath: StringProperty(subtype="FILE_PATH")
    files: CollectionProperty(type=PropertyGroup)
    filter_folder: BoolProperty(default=True, options={"HIDDEN"})
    filter_image: BoolProperty(default=True, options={"HIDDEN"})
    target_property: StringProperty(options={"HIDDEN"})

    relative_path: BoolProperty(
        name="Relative Path", description="Select the file relative to the blend file", default=True)

    disabled_message = "Can't open/assign images to linked data blocks. Please make it local first"

    @ classmethod
    def description(cls, context, properties):
        description_text = "Load an external image "
        if bpy.app.version < (3, 0, 0) and is_linked(context.host):
            description_text += f"\nDisabled: {cls.disabled_message}"

        return description_text

    @ classmethod
    def poll(cls, context):
        if hasattr(context, "host"):
            if is_linked(context.host):
                if bpy.app.version >= (3, 0, 0):
                    cls.poll_message_set(f"{cls.disabled_message}.")
                return False

        return True

    def execute(self, context):
        if not self.files[0].name:
            self.report({'INFO'}, "Open image cancelled. No image selected.")
            return {'CANCELLED'}

        old_img = getattr(self.target, self.target_property)

        # Load/Reload the first image and assign it to the target property, then load the rest of the images if they're not already loaded. This mimics Blender's default open files behavior.
        # self.files is sorted alphabetically by Blender, self.files[0] is the 1. of the selection in alphabetical order
        primary_filepath = os.path.join(self.directory, self.files[0].name)
        primary_img = bpy.data.images.load(
            filepath=primary_filepath, check_existing=True)
        primary_img.reload()
        setattr(self.target, self.target_property, primary_img)

        for f in self.files[1:]:
            bpy.data.images.load(filepath=os.path.join(
                self.directory, f.name), check_existing=True)

        update_image_editors(old_img, primary_img)
        redraw_component_ui(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.target = context.target

        last_image = getattr(self.target, self.target_property)
        if type(last_image) is bpy.types.Image:  # if the component has been assigned before, get its filepath
            self.filepath = last_image.filepath  # start the file browser at the location of the previous file

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BakeLightmaps(Operator):
    bl_idname = "object.bake_lightmaps"
    bl_label = "Bake Lightmaps"
    bl_description = "Bake lightmaps of selected objects using the Cycles render engine and pack them into the .blend."
    bl_options = {'REGISTER', 'UNDO'}

    default_intensity: FloatProperty(name="Lightmaps Intensity",
                                     default=3.14,
                                     description="Multiplier for hubs on how to interpret the brightness of the image. Set this to 1.0 if you have set up the lightmaps manually and use a non-HDR format like png or jpg.")
    resolution: IntProperty(name="Lightmaps Resolution",
                            default=2048,
                            description="The pixel resolution of the resulting lightmap.")
    samples: IntProperty(name="Max Samples",
                         default=1024,
                         description="The number of samples to use for baking. Higher values reduce noise but take longer.")

    def create_uv_layouts(self, context, mesh_objs):
        # set up UV layer structure. The first layer has to be UV0, the second one LIGHTMAP_LAYER_NAME for the lightmap.
        for obj in mesh_objs:
            obj_uv_layers = obj.data.uv_layers
            # Check whether there are any UV layers and if not, create the two that are required.
            if len(obj_uv_layers) == 0:
                obj_uv_layers.new(name='UV0')
                obj_uv_layers.new(name=LIGHTMAP_LAYER_NAME)

            # In case there is only one UV layer create a second one named LIGHTMAP_LAYER_NAME for the lightmap.
            if len(obj_uv_layers) == 1:
                obj_uv_layers.new(name=LIGHTMAP_LAYER_NAME)
            # Check if object has a second UV layer. If it is named LIGHTMAP_LAYER_NAME, assume it is used for the lightmap.
            # Otherwise add a new UV layer LIGHTMAP_LAYER_NAME and place it second in the slot list.
            elif obj_uv_layers[1].name != LIGHTMAP_LAYER_NAME:
                print("The second UV layer in hubs should be named " + LIGHTMAP_LAYER_NAME + " and is reserved for the lightmap, all the layers >1 are ignored.")
                obj_uv_layers.new(name=LIGHTMAP_LAYER_NAME)
                # The new layer is the last in the list, swap it for position 1
                obj_uv_layers[1], obj_uv_layers[-1] = obj_uv_layers[-1], obj_uv_layers[1]

            # The layer for the lightmap needs to be the active one before lightmap packing
            obj_uv_layers.active = obj_uv_layers[LIGHTMAP_LAYER_NAME]
            # Set the object as selected in object mode 
            obj.select_set(True)

        # run UV lightmap packing on all selected objects
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # TODO: We need to warn the user at some place like the README that the uv_layer[1] gets completely overwritten if it is called 'UV1'
        # bpy.ops.uv.lightmap_pack()
        bpy.ops.uv.smart_project(island_margin=LIGHTMAP_UV_ISLAND_MARGIN)
        bpy.ops.object.mode_set(mode='OBJECT')
        # Deselct the objects again to return without changing the scene
        for obj in mesh_objs:
            obj.select_set(False)
        # Update the view layer so all parts take notice of the changed UV layout
        bpy.context.view_layer.update()

        return{'FINISHED'}
    
    def execute(self, context):
        # Check selected objects
        selected_objects = bpy.context.selected_objects

        # filter mesh objects and others
        mesh_objs, other_objs = [], []
        for ob in selected_objects:
            (mesh_objs if ob.type == 'MESH' else other_objs).append(ob)
            # Remove all objects from selection so we can easily re-select subgroups later
            ob.select_set(False)

        # for ob in other_objs:
            # Remove non-mesh objects from selection to ensure baking will work
            # ob.select_set(False)

        # Gather all materials on the selected objects
        # materials = []
        # Dictionary that stores which object has which materials so we can group them later
        material_object_associations = {}
        for obj in mesh_objs:
            if len(obj.material_slots) >= 1:
                # TODO: Make more efficient
                for slot in obj.material_slots:
                    if slot.material is not None:
                        mat = slot.material
                        if mat not in material_object_associations:
                            # materials.append(mat)
                            material_object_associations[mat] = []
                        material_object_associations[mat].append(obj)
            else:
                # an object without materials should not be selected when running the bake operator
                print("Object " + obj.name + " does not have material slots, removing from set")
                obj.select_set(False)
                mesh_objs.remove(obj)

        print(material_object_associations.items())
        # Set up the UV layer structure and auto-unwrap optimized for lightmaps
        visited_objects = set()
        for mat, obj_list in material_object_associations.items():
            for ob in visited_objects:
                if ob in obj_list:
                    obj_list.remove(ob)
            self.create_uv_layouts(context, obj_list)
            for ob in obj_list:
                visited_objects.add(ob)

        # Check for the required nodes and set them up if not present
        lightmap_texture_nodes = []
        for mat in material_object_associations.keys():
            mat_nodes = mat.node_tree.nodes
            lightmap_nodes = [node for node in mat_nodes if node.bl_idname == 'moz_lightmap.node']
            if len(lightmap_nodes) > 1:
                print("Too many lightmap nodes in node tree of material", mat.name)
            elif len(lightmap_nodes) < 1:
                lightmap_texture_nodes.append(self.setup_moz_lightmap_nodes(mat.node_tree))
            else:
                # TODO: Check wether all nodes are set up correctly, for now assume they are
                lightmap_nodes[0].intensity = self.default_intensity
                # the image texture node needs to be the active one for baking, it is connected to the lightmap node so get it from there
                lightmap_texture_node = lightmap_nodes[0].inputs[0].links[0].from_node
                mat.node_tree.nodes.active = lightmap_texture_node
                lightmap_texture_nodes.append(lightmap_texture_node)

        # Re-select all the objects that need baking before running the operator
        for ob in mesh_objs:
            ob.select_set(True)
        # Baking has to happen in Cycles, it is not supported in EEVEE yet
        render_engine_tmp = context.scene.render.engine
        context.scene.render.engine = 'CYCLES'
        samples_tmp = context.scene.cycles.samples
        context.scene.cycles.samples = self.samples
        # Baking needs to happen without the color pass because we only want the direct and indirect light contributions
        bake_settings_before = context.scene.render.bake
        bake_settings = context.scene.render.bake
        bake_settings.use_pass_direct = True
        bake_settings.use_pass_indirect = True
        bake_settings.use_pass_color = False
        # The should be small because otherwise it could overwrite UV islands
        bake_settings.margin = 2
        # Not sure whether this has any influence
        bake_settings.image_settings.file_format = 'HDR'
        context.scene.render.image_settings.file_format = 'HDR'
        bpy.ops.object.bake(type='DIFFUSE')
        # After baking is done, return everything back to normal
        context.scene.cycles.samples = samples_tmp
        context.scene.render.engine = render_engine_tmp
        # Pack all newly created or updated images
        for node in lightmap_texture_nodes:
            file_path = bpy.path.abspath(f"{bpy.app.tempdir}/{node.image.name}.hdr")
            # node.image.save_render(file_path)
            node.image.filepath_raw = file_path
            node.image.file_format = 'HDR'
            node.image.save()
            node.image.pack()
            # Update the filepath so it unpacks nicely for the user.
            # TODO: Mechanism taken from reflection_probe.py line 300-306, de-duplicate
            new_filepath = f"//{node.image.name}.hdr"
            node.image.packed_files[0].filepath = new_filepath
            node.image.filepath_raw = new_filepath
            node.image.filepath = new_filepath

            # Remove file from temporary directory to de-clutter the system. Especially on windows the temporary directory is rarely purged.
            if os.path.exists(file_path):
                os.remove(file_path)

        # return to old settings
        bake_settings = bake_settings_before
        context.scene.cycles.samples = samples_tmp
        context.scene.render.engine = render_engine_tmp

        return {'FINISHED'}

    def invoke(self, context, event):
        # needed to get the dialoge with the intensity
        return context.window_manager.invoke_props_dialog(self)

    def setup_moz_lightmap_nodes(self, node_tree):
        ''' Returns the lightmap texture node of the newly created setup '''
        mat_nodes = node_tree.nodes
        # This function gets called when no lightmap node is present
        lightmap_node = mat_nodes.new(type="moz_lightmap.node")
        lightmap_node.intensity = self.default_intensity

        lightmap_texture_node = mat_nodes.new(type="ShaderNodeTexImage")
        lightmap_texture_node.location[0] -= 300

        img = bpy.data.images.new('LightMap', self.resolution, self.resolution, alpha=False, float_buffer=True)
        lightmap_texture_node.image = img
        if bpy.app.version < (4, 0, 0):
            lightmap_texture_node.image.colorspace_settings.name = "Linear"
        else:
            lightmap_texture_node.image.colorspace_settings.name = "Linear Rec.709"

        UVmap_node = mat_nodes.new(type="ShaderNodeUVMap")
        UVmap_node.uv_map = "UV1"
        UVmap_node.location[0] -= 500

        node_tree.links.new(UVmap_node.outputs['UV'], lightmap_texture_node.inputs['Vector'])
        node_tree.links.new(lightmap_texture_node.outputs['Color'], lightmap_node.inputs['Lightmap'])

        # the image texture node needs to be the active one for baking
        node_tree.nodes.active = lightmap_texture_node

        return lightmap_texture_node


def register():
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)
    bpy.utils.register_class(MigrateHubsComponents)
    bpy.utils.register_class(UpdateHubsGizmos)
    bpy.utils.register_class(ReportViewer)
    bpy.utils.register_class(ReportScroller)
    bpy.utils.register_class(ViewLastReport)
    bpy.utils.register_class(ViewReportInInfoEditor)
    bpy.utils.register_class(CopyHubsComponent)
    bpy.utils.register_class(OpenImage)
    bpy.utils.register_class(BakeLightmaps)
    bpy.types.WindowManager.hubs_report_scroll_index = IntProperty(
        default=0, min=0)
    bpy.types.WindowManager.hubs_report_scroll_percentage = IntProperty(
        name="Scroll Position", default=0, min=0, max=100, subtype='PERCENTAGE')
    bpy.types.WindowManager.hubs_report_last_title = StringProperty()
    bpy.types.WindowManager.hubs_report_last_report_string = StringProperty()


def unregister():
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
    bpy.utils.unregister_class(MigrateHubsComponents)
    bpy.utils.unregister_class(UpdateHubsGizmos)
    bpy.utils.unregister_class(ReportViewer)
    bpy.utils.unregister_class(ReportScroller)
    bpy.utils.unregister_class(ViewLastReport)
    bpy.utils.unregister_class(ViewReportInInfoEditor)
    bpy.utils.unregister_class(CopyHubsComponent)
    bpy.utils.unregister_class(OpenImage)
    bpy.utils.unregister_class(BakeLightmaps)
    del bpy.types.WindowManager.hubs_report_scroll_index
    del bpy.types.WindowManager.hubs_report_scroll_percentage
    del bpy.types.WindowManager.hubs_report_last_title
    del bpy.types.WindowManager.hubs_report_last_report_string
