import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from functools import reduce

from .types import PanelType
from .utils import get_object_source, dash_to_title, has_component, add_component, remove_component
from .components_registry import get_components_registry, get_components_icons
from ..preferences import get_addon_pref


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

        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        panel_type = self.panel_type

        # Filter components that are not targeted to this object type or their poll method call returns False
        def filter_source_type(cmp):
            (_, component_class) = cmp
            return not component_class.is_dep_only() and PanelType(panel_type) in component_class.get_panel_type() and component_class.poll(context, PanelType(panel_type))

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
        context.area.tag_redraw()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)


def unregister():
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
