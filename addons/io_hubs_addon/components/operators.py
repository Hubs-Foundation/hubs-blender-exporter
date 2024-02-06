import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty
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
    return [f"{i+1:02d}   {message}" for i, message in enumerate(report_string.split("\n\n"))]


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

    filepath: StringProperty(subtype="FILE_PATH")
    files: CollectionProperty(type=PropertyGroup)
    filter_folder: BoolProperty(default=True, options={"HIDDEN"})
    filter_image: BoolProperty(default=True, options={"HIDDEN"})
    target_property: StringProperty()

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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "relative_path")

    def execute(self, context):
        #dirname = os.path.dirname(self.filepath) #fails if path selected in the Blender File View is relative (starts with //)
        abs_dir = bpy.path.abspath(self.filepath) # converts relative paths to absolute ones eg //MyPath -> C:\MyPath
        #or:
        #abs_dir = self.filepath if not self.relative_path else bpy.path.abspath(self.filepath)
        dirname = os.path.dirname(abs_dir)

        if not self.files[0].name:
            self.report({'INFO'}, "Open image cancelled.  No image selected.")
            return {'CANCELLED'}

        old_img = self.hubs_component[self.target_property]

        # Load/Reload the first image and assign it to the target property, then load the rest of the images if they're not already loaded. This mimics Blender's default open files behavior.
        primary_filepath = os.path.join(dirname, self.files[0].name)
        primary_img = bpy.data.images.load(
            filepath=primary_filepath, check_existing=True)
        primary_img.reload()
        self.hubs_component[self.target_property] = primary_img

        for f in self.files[1:]:
            bpy.data.images.load(filepath=os.path.join(
                dirname, f.name), check_existing=True)

        update_image_editors(old_img, primary_img)
        redraw_component_ui(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = ""
        self.hubs_component = context.hubs_component
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


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
    del bpy.types.WindowManager.hubs_report_scroll_index
    del bpy.types.WindowManager.hubs_report_scroll_percentage
    del bpy.types.WindowManager.hubs_report_last_title
    del bpy.types.WindowManager.hubs_report_last_report_string
