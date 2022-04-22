import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from functools import reduce

from .types import PanelType
from .utils import add_gizmo, get_object_source, dash_to_title, has_component, add_component, remove_component, remove_gizmo
from .components_registry import get_components_registry, get_components_icons


class AddHubsComponent(Operator):
    bl_idname = "wm.add_hubs_component"
    bl_label = "Add Hubs Component"
    bl_property = "component_id"

    panel_type: StringProperty(name="panel_type")
    component_id: StringProperty(name="component_id")
    gizmo: StringProperty(name="gizmo")

    def execute(self, context):
        if self.component_id == '':
            return

        obj = get_object_source(context, self.panel_type)

        add_component(
            obj,
            self.component_id
        )
        add_gizmo(obj, self.gizmo)

        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        panel_type = self.panel_type

        # Filter components that are not targeted to this object type or their poll method call returns False
        def filter_source_type(cmp):
            (_, component_class) = cmp
            return component_class.get_panel_type() == PanelType(panel_type) and component_class.poll(context)

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
            row = self.layout.row()
            for category, cmps in components_by_category.items():
                column = row.column()
                column.label(text=category)

                for (component_name, component_class) in cmps:
                    if component_class.is_dep_only():
                        continue

                    component_id = component_class.get_id()
                    component_display_name = dash_to_title(
                        component_class.get_display_name(component_name))

                    if has_component(obj, component_id):
                        column.label(text=component_display_name)
                    else:
                        op = None
                        if component_class.get_icon() is not None:
                            icon = component_class.get_icon()
                            op = column.operator(
                                AddHubsComponent.bl_idname, text=component_display_name, icon_value=components_icons[icon].icon_id)
                        else:
                            op = column.operator(
                                AddHubsComponent.bl_idname, text=component_display_name, icon='ADD')
                        op.component_id = component_id
                        op.gizmo = component_class.get_gizmo()
                        op.panel_type = panel_type

                    added_comps += 1

            if added_comps == 0:
                column = row.column()
                column.label(
                    text="No components available for this object type")

        bpy.context.window_manager.popup_menu(draw)

        return {'RUNNING_MODAL'}


class RemoveHubsComponent(Operator):
    bl_idname = "wm.remove_hubs_component"
    bl_label = "Remove Hubs Component"

    panel_type: StringProperty(name="panel_type")
    component_id: StringProperty(name="component_id")
    gizmo: StringProperty(name="gizmo")

    def execute(self, context):
        if self.component_id == '':
            return
        obj = get_object_source(context, self.panel_type)
        remove_component(obj, self.component_id)
        if self.gizmo:
            remove_gizmo(obj, self.gizmo)
        context.area.tag_redraw()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)


def unregister():
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
