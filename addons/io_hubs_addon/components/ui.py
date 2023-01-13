import bpy
from bpy.props import StringProperty
from .types import PanelType
from .components_registry import get_component_by_name, get_components_registry
from .utils import get_object_source, is_linked


def draw_component_global(panel, context):
    layout = panel.layout
    components_registry = get_components_registry()
    for _, component_class in components_registry.items():
        component_class.draw_global(context, layout, panel)


def draw_component(panel, context, obj, row, component_item):
    component_name = component_item.name
    component_class = get_component_by_name(component_name)
    if component_class:
        panel_type = PanelType(panel.bl_context)
        if panel_type not in component_class.get_panel_type() or not component_class.poll(panel_type, obj, ob=context.object):
            col = row.box().column()
            top_row = col.row()
            top_row.label(
                text=f"Unsupported host for component '{component_class.get_display_name()}'", icon="ERROR")
            remove_component_operator = top_row.operator(
                "wm.remove_hubs_component",
                text="",
                icon="X"
            )
            remove_component_operator.component_name = component_name
            remove_component_operator.panel_type = panel.bl_context
            return

        component_id = component_class.get_id()
        component = getattr(obj, component_id)

        has_properties = len(component_class.get_properties()) > 0

        col = row.box().column()
        top_row = col.row()

        if has_properties:
            top_row.prop(component_item, "expanded",
                         icon="TRIA_DOWN" if component_item.expanded else "TRIA_RIGHT",
                         icon_only=True, emboss=False
                         )

        display_name = component_class.get_display_name()

        top_row.label(text=display_name)

        if has_properties or not component_class.is_dep_only():
            top_row.context_pointer_set("panel", panel)
            copy_component_operator = top_row.operator(
                "wm.copy_hubs_component",
                text="",
                icon="PASTEDOWN"
            )
            copy_component_operator.component_name = component_name
            copy_component_operator.panel_type = panel.bl_context

        if not (component_class.is_dep_only() or component_item.isDependency):
            top_row.context_pointer_set("panel", panel)
            remove_component_operator = top_row.operator(
                "wm.remove_hubs_component",
                text="",
                icon="X"
            )
            remove_component_operator.component_name = component_name
            remove_component_operator.panel_type = panel.bl_context

        body_col = col.column()
        body_col.enabled = not is_linked(obj)
        if component_item.expanded:
            component.draw(context, body_col, panel)

    else:
        col = row.box().column()
        top_row = col.row()
        top_row.label(
            text=f"Unknown component '{component_name}'", icon="ERROR")
        top_row.context_pointer_set("panel", panel)
        remove_component_operator = top_row.operator(
            "wm.remove_hubs_component",
            text="",
            icon="X"
        )
        remove_component_operator.component_name = component_name
        remove_component_operator.panel_type = panel.bl_context


def draw_components_list(panel, context):
    layout = panel.layout

    obj = get_object_source(context, panel.bl_context)

    if not obj:
        return

    layout.context_pointer_set("panel", panel)
    add_component_operator = layout.operator(
        "wm.add_hubs_component",
        text="Add Component",
        icon="ADD"
    )
    add_component_operator.panel_type = panel.bl_context

    for component_item in obj.hubs_component_list.items:
        row = layout.row()
        draw_component(panel, context, obj, row, component_item)

    layout.separator()


def add_link_indicator(layout, datablock):
    if datablock.library:
        library = datablock.library
        icon = 'LINKED'
    else:
        library = datablock.override_library.reference.library
        icon = 'LIBRARY_DATA_OVERRIDE'

    tooltip = (
        f"{datablock.name}\n"
        f"\n"
        f"Source Library:\n"
        f"[{library.name}]\n"
        f"{library.filepath}"
    )
    layout.operator("ui.hubs_tooltip_label", text='',
                    icon=icon).tooltip = tooltip


class HubsObjectPanel(bpy.types.Panel):
    bl_label = "Hubs"
    bl_idname = "OBJECT_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        draw_components_list(self, context)


def export_scene():
    try:
        import os
        import sys
        extension = '.glb'
        output_dir = "/Users"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        args = {
            # Settings from "Remember Export Settings"
            **dict(bpy.context.scene.get('glTF2ExportSettings', {})),

            'export_format': ('GLB' if extension == '.glb' else 'GLTF_SEPARATE'),
            'filepath': os.path.join("/Users/manuelmartin/Documents/3D/hubs/", "scene.glb"),
            'export_cameras': True,
            'export_lights': True,
            'export_extras': True,
            'use_visible': True
        }
        bpy.ops.export_scene.gltf(**args)
    except Exception as err:
        print(err, file=sys.stderr)


web_driver = None


def refresh_scene_viewer():
    import os
    from selenium.webdriver.common.by import By
    web_driver.find_element(
        By.XPATH, "//input[@type='file']").send_keys(os.path.join("/Users/manuelmartin/Documents/3D/hubs/", "scene.glb"))


class HubsSceneViewOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.view_scene"
    bl_label = "Remove Track"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        export_scene()

        global web_driver
        if not web_driver:
            from selenium import webdriver
            web_driver = webdriver.Firefox()
            # driver = webdriver.Chrome(executable_path='chromedriver.exe')
            # for selenium4 do this ( if above line gives error) run the next two lines:
            ## service = Service(executable_path='C:\Program Files\Chrome Driver\chromedriver.exe')
            # driver = webdriver.Chrome(service=service)driver.implicitly_wait(15)

            # disable the OS file picker
            web_driver.execute_script("""
                document.addEventListener('click', function(evt) {
                if (evt.target.type === 'file')
                    evt.preventDefault();
                }, true)
                """)

            web_driver.get('https://hubs.local:8080/viewer.html')

        refresh_scene_viewer()

        return {'FINISHED'}


class HubsScenePanel(bpy.types.Panel):
    bl_label = 'Hubs'
    bl_idname = "SCENE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        draw_component_global(self, context)
        layout = self.layout
        layout.separator()
        layout.operator(HubsSceneViewOperator.bl_idname, text='View scene')
        layout.separator()
        draw_components_list(self, context)


class HubsMaterialPanel(bpy.types.Panel):
    bl_label = 'Hubs'
    bl_idname = "MATERIAL_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        draw_components_list(self, context)


class HubsBonePanel(bpy.types.Panel):
    bl_label = "Hubs"
    bl_idname = "BONE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    def draw(self, context):
        draw_components_list(self, context)


class TooltipLabel(bpy.types.Operator):
    bl_idname = "ui.hubs_tooltip_label"
    bl_label = "---"

    tooltip: StringProperty(default=" ")

    @ classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'CANCELLED'}


def window_menu_addition(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("wm.hubs_view_last_report")


def object_menu_addition(self, context):
    layout = self.layout
    layout.separator()
    op = layout.operator("wm.migrate_hubs_components")
    op.is_registration = False


def gizmo_display_popover_addition(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("wm.update_hubs_gizmos")


def register():
    bpy.utils.register_class(HubsSceneViewOperator)
    bpy.utils.register_class(HubsObjectPanel)
    bpy.utils.register_class(HubsScenePanel)
    bpy.utils.register_class(HubsMaterialPanel)
    bpy.utils.register_class(HubsBonePanel)
    bpy.utils.register_class(TooltipLabel)

    bpy.types.TOPBAR_MT_window.append(window_menu_addition)
    bpy.types.VIEW3D_MT_object.append(object_menu_addition)
    bpy.types.VIEW3D_PT_gizmo_display.append(gizmo_display_popover_addition)


def unregister():
    bpy.utils.unregister_class(HubsObjectPanel)
    bpy.utils.unregister_class(HubsScenePanel)
    bpy.utils.unregister_class(HubsMaterialPanel)
    bpy.utils.unregister_class(HubsBonePanel)
    bpy.utils.unregister_class(TooltipLabel)
    bpy.utils.unregister_class(HubsSceneViewOperator)

    bpy.types.TOPBAR_MT_window.remove(window_menu_addition)
    bpy.types.VIEW3D_MT_object.remove(object_menu_addition)
    bpy.types.VIEW3D_PT_gizmo_display.remove(gizmo_display_popover_addition)

    global web_driver
    if web_driver:
        web_driver.close()
