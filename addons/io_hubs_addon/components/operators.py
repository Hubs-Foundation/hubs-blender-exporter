import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import Operator
from functools import reduce

from .types import PanelType, MigrationType
from .utils import get_object_source, dash_to_title, has_component, add_component, remove_component, wrap_text, display_wrapped_text
from .components_registry import get_components_registry, get_components_icons
from ..preferences import get_addon_pref
from .handlers import migrate_components
from .gizmos import update_gizmos


class AddHubsComponent(Operator):
    bl_idname = "wm.add_hubs_component"
    bl_label = "Add Hubs Component"
    bl_property = "component_name"
    bl_options = {'REGISTER', 'UNDO'}

    panel_type: StringProperty(name="panel_type")
    component_name: StringProperty(name="component_name")

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
        components_icons = get_components_icons()
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
                        component_display_name = dash_to_title(
                            component_class.get_display_name(component_name))

                        op = None
                        if component_class.get_icon() is not None:
                            icon = component_class.get_icon()
                            if icon.find('.') != -1:
                                if has_component(obj, component_name):
                                    op = column.label(
                                        text=component_display_name, icon_value=components_icons[icon].icon_id)
                                else:
                                    op = column.operator(
                                        AddHubsComponent.bl_idname, text=component_display_name,
                                        icon_value=components_icons[icon].icon_id)
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

        return {'RUNNING_MODAL'}


class RemoveHubsComponent(Operator):
    bl_idname = "wm.remove_hubs_component"
    bl_label = "Remove Hubs Component"
    bl_options = {'REGISTER', 'UNDO'}

    panel_type: StringProperty(name="panel_type")
    component_name: StringProperty(name="component_name")

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


class GenerateNavMesh(Operator):
    bl_idname = "object.generate_hubs_navmesh"
    bl_label = "Generate Hubs Navigation Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import bmesh

        objs = bpy.context.selected_objects

        # Check if any objects are selected. If none, abort.
        if len(objs) == 0:
            return {'FINISHED'}

        # Make sure there's a mesh object set as active. If not, check if it's a meta object. If yes, convert it to mesh. If not, abort
        for obj in objs:
            if obj is not None:
                if obj.type != "MESH":
                    if obj.type == "META":
                        bpy.ops.object.convert(target='MESH')
                    else:
                        return {'FINISHED'}
            else:
                return {'FINISHED'}

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'}, TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_axis_ortho": 'X', "orient_type": 'GLOBAL', "orient_matrix": (
            (0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type": 'GLOBAL', "constraint_axis": (False, False, False), "mirror": False})

        # Check if there's more than one selected object. If so, join them all together.
        if len(objs) > 1:
            bpy.ops.object.join()

        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        obj = bpy.context.active_object

        bpy.ops.object.make_single_user(object=True, obdata=True)

        # Apply all current modifiers
        if len(bpy.context.active_object.modifiers) > 0:
            for modifier in bpy.context.active_object.modifiers:
                bpy.ops.object.modifier_apply(modifier=modifier.name)

        bpy.ops.object.transform_apply(
            location=False, rotation=True, scale=True)

        # Solidify modifier - TODO

        # bpy.ops.object.modifier_add(type='SOLIDIFY')
        # bpy.context.object.modifiers["Solidify"].thickness = 1
        # bpy.ops.object.modifier_apply(modifier="Solidify")

        # # # Remesh modifier   - TODO

        # bpy.ops.object.modifier_add(type='REMESH')
        # bpy.context.object.modifiers["Remesh"].voxel_size = .1
        # bpy.context.object.modifiers["Remesh"].adaptivity = 0
        # bpy.ops.object.modifier_apply(modifier="Remesh")

        # # Post-modifier cleanup   - TODO

        # bpy.ops.object.mode_set(mode="EDIT")
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.dissolve_limited(
        #     angle_limit=0.0872665, use_dissolve_boundaries=False, delimit={'NORMAL'})
        # bpy.ops.mesh.quads_convert_to_tris(
        #     quad_method='BEAUTY', ngon_method='BEAUTY')
        # bpy.ops.object.mode_set(mode="OBJECT")

        # Begin bmesh ops
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # Get a list of steep faces
        not_walkable = list()
        for f in bm.faces:
            if f.normal[2] < 0.6:
                not_walkable.append(f)
            f.smooth = True
        bmesh.ops.delete(bm, geom=not_walkable, context='FACES')
        bmesh.ops.holes_fill(bm, edges=bm.edges, sides=6)

        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()

        # Lower the polygon count
        bmesh.ops.dissolve_limit(
            bm, angle_limit=0.0872665, use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={"NORMAL"})
        bmesh.ops.connect_verts_concave(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces,
                              quad_method="BEAUTY", ngon_method="BEAUTY")

        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1.0)

        # Finalize
        me_nav = bpy.data.meshes.new("NavMesh")
        bm.to_mesh(me_nav)
        bm.free()
        obj.data = me_nav
        obj.name = "Navigation Mesh"
        obj.select_set(True)
        bpy.ops.wm.add_hubs_component(
            panel_type="object", component_name="nav-mesh")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode="OBJECT")

        # Navmesh material
        if "navmesh" not in bpy.data.materials.keys():
            bpy.data.materials.new("navmesh")
        bpy.context.active_object.data.materials.append(
            bpy.data.materials["navmesh"])
        bpy.context.active_object.data.materials[0].diffuse_color = (
            1, 0, 0.78315, 1)

        return {'FINISHED'}


def split_and_prefix_report_messages(report_string):
    return [f"{i+1:02d}   {message}" for i, message in enumerate(report_string.split("\n\n"))]


def register():
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)
    bpy.utils.register_class(MigrateHubsComponents)
    bpy.utils.register_class(GenerateNavMesh)
    bpy.utils.register_class(UpdateHubsGizmos)
    bpy.utils.register_class(ReportViewer)
    bpy.utils.register_class(ReportScroller)
    bpy.utils.register_class(ViewLastReport)
    bpy.utils.register_class(ViewReportInInfoEditor)
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
    bpy.utils.unregister_class(GenerateNavMesh)
    bpy.utils.unregister_class(UpdateHubsGizmos)
    bpy.utils.unregister_class(ReportViewer)
    bpy.utils.unregister_class(ReportScroller)
    bpy.utils.unregister_class(ViewLastReport)
    bpy.utils.unregister_class(ViewReportInInfoEditor)
    del bpy.types.WindowManager.hubs_report_scroll_index
    del bpy.types.WindowManager.hubs_report_scroll_percentage
    del bpy.types.WindowManager.hubs_report_last_title
    del bpy.types.WindowManager.hubs_report_last_report_string
