import os
import json
import datetime
import bpy
from bpy.props import IntVectorProperty, BoolProperty, FloatProperty, StringProperty
from bpy.props import PointerProperty, FloatVectorProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup, Panel, Operator, Menu
from bpy.app.handlers import persistent
from io_scene_gltf2.blender.exp import gltf2_blender_gather, gltf2_blender_gather_nodes
from io_scene_gltf2.blender.exp.gltf2_blender_gltf2_exporter import GlTF2Exporter
from io_scene_gltf2.io.exp import gltf2_io_export
from io_scene_gltf2.io.com import gltf2_io_extensions
from io_scene_gltf2.blender.com import gltf2_blender_json

bl_info = {
    "name" : "io_scene_hubs",
    "author" : "Robert Long",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

# Get the path to the default config file
paths = bpy.utils.script_paths("addons")

default_config_filename = 'default-config.json'
default_config_path = default_config_filename

for path in paths:
    default_config_path = os.path.join(path, "io_scene_hubs", default_config_filename)
    if os.path.exists(default_config_path):
        break

bpy.hubs_config = None
bpy.registered_hubs_components = {}

class HubsComponentName(PropertyGroup):
    name: bpy.props.StringProperty(name="name")

class HubsComponentList(PropertyGroup):
    items: bpy.props.CollectionProperty(type=HubsComponentName)

class HubsSettings(PropertyGroup):
    def config_updated(self, _context):
        self.reload_config()

    def reload_config(self):
        self.load_config(self.config_path)

    def load_config(self, config_path):
        if os.path.splitext(config_path)[1] == '.json':
            with open(bpy.path.abspath(config_path)) as config_file:
                bpy.hubs_config = json.load(config_file)
        else:
            print('Config must be a .json file!')

        try:
            for component_name, component_class in bpy.registered_hubs_components.items():
                component_class_name = "hubs_component_%s" % component_name.replace('-', '_')
                delattr(bpy.types.Object, component_class_name)
                bpy.utils.unregister_class(component_class)
        except UnboundLocalError:
            pass
        bpy.registered_hubs_components = {}

        for component_name, component_definition in bpy.hubs_config['components'].items():
            component_class_name = "hubs_component_%s" % component_name.replace('-', '_')
            component_property_dict = {}

            for property_name, property_definition in component_definition['properties'].items():
                property_type = property_definition['type']

                if property_type == 'int':
                    component_property_dict[property_name] = IntProperty(
                        name=property_name
                    )
                elif property_type == 'float':
                    component_property_dict[property_name] = FloatProperty(
                        name=property_name
                    )
                elif property_type == 'bool':
                    component_property_dict[property_name] = BoolProperty(
                        name=property_name
                    )
                elif property_type == 'string':
                    component_property_dict[property_name] = StringProperty(
                        name=property_name
                    )
                elif property_type == 'ivec2':
                    component_property_dict[property_name] = IntVectorProperty(
                        name=property_name,
                        size=2
                    )
                elif property_type == 'ivec3':
                    component_property_dict[property_name] = IntVectorProperty(
                        name=property_name,
                        size=3
                    )
                elif property_type == 'ivec4':
                    component_property_dict[property_name] = IntVectorProperty(
                        name=property_name,
                        size=4
                    )
                elif property_type == 'vec2':
                    component_property_dict[property_name] = FloatVectorProperty(
                        name=property_name,
                        size=2
                    )
                elif property_type == 'vec3':
                    component_property_dict[property_name] = FloatVectorProperty(
                        name=property_name,
                        size=3
                    )
                elif property_type == 'vec4':
                    component_property_dict[property_name] = FloatVectorProperty(
                        name=property_name,
                        size=4
                    )
                elif property_type == 'color':
                    component_property_dict[property_name] = FloatVectorProperty(
                        name=property_name,
                        subtype='COLOR',
                        default=(1.0, 1.0, 1.0, 1.0),
                        size=4,
                        min=0,
                        max=1
                    )
                else:
                    raise TypeError('Unsupported Hubs property type \'%s\' for %s on %s' % (
                        property_type, property_name, component_name))

            component_class = type(component_class_name, (PropertyGroup,), component_property_dict)
            bpy.utils.register_class(component_class)
            setattr(bpy.types.Object, component_class_name, PointerProperty(type=component_class))
            bpy.registered_hubs_components[component_name] = component_class

    config_path: StringProperty(
        name="config_path",
        description="Path to the config file",
        default=default_config_path,
        options={'HIDDEN'},
        maxlen=1024,
        subtype='FILE_PATH',
        update=config_updated
    )

class AddHubsComponentMenu(Menu):
    bl_label = "Add Hubs Component"
    bl_idname = "OBJECT_MT_add_hubs_component_menu"

    def draw(self, context):
        layout = self.layout

        for component_name in bpy.registered_hubs_components:
            layout.operator(
                "wm.add_hubs_component",
                text=component_name
            ).component_name = component_name

class HubsObjectPanel(Panel):
    bl_label = "Hubs"
    bl_idname = "OBJECT_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if bpy.hubs_config is None:
            return

        for component_item in obj.hubs_component_list.items:
            component_name = component_item.name
            component_definition = bpy.hubs_config['components'][component_name]
            component_class = bpy.registered_hubs_components[component_name]
            component_class_name = component_class.__name__
            component = getattr(obj, component_class_name)

            row = layout.row()
            row.label(text=component_name)
            row.operator(
                "wm.remove_hubs_component",
                text="",
                icon="X"
            ).component_name = component_name

            split = layout.split(factor=0.1)
            col = split.column()
            col.label(text=" ")
            col = split.column()
            for property_name, _property_definition in component_definition['properties'].items():
                col.prop(data=component, property=property_name)

        layout.separator()

        layout.operator(
            "wm.call_menu",
            text="Add Component"
        ).name = "OBJECT_MT_add_hubs_component_menu"

class HubsSettingsPanel(Panel):
    bl_label = 'Hubs'
    bl_idname = "SCENE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene.hubs_settings, "config_path", text="Config File")
        row.operator("wm.reload_hubs_config", text="", icon="FILE_REFRESH")

        row = layout.row()
        row.operator("wm.export_hubs_gltf", text="Export Scene")
        row.operator("wm.export_hubs_gltf", text="Export Selected").selected = True

class AddHubsComponent(Operator):
    bl_idname = "wm.add_hubs_component"
    bl_label = "Add Hubs Component"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        obj = context.object
        item = obj.hubs_component_list.items.add()
        item.name = self.component_name
        context.area.tag_redraw()
        return {'FINISHED'}

class RemoveHubsComponent(Operator):
    bl_idname = "wm.remove_hubs_component"
    bl_label = "Remove Hubs Component"

    component_name: StringProperty(name="component_name")

    def execute(self, context):
        if self.component_name == '':
            return

        obj = context.object
        items = obj.hubs_component_list.items
        items.remove(items.find(self.component_name))
        context.area.tag_redraw()
        return {'FINISHED'}

class ReloadHubsConfig(Operator):
    bl_idname = "wm.reload_hubs_config"
    bl_label = "Reload Hubs Config"

    def execute(self, context):
        context.scene.hubs_settings.reload_config()
        context.area.tag_redraw()
        return {'FINISHED'}

class ExportHubsGLTF(Operator):
    bl_idname = "wm.export_hubs_gltf"
    bl_label = "Export Hubs GLTF"

    selected: BoolProperty(name="selected", default=False)

    def __fix_json(self, obj):
        # TODO: move to custom JSON encoder
        fixed = obj
        if isinstance(obj, dict):
            fixed = {}
            for key, value in obj.items():
                if not self.__should_include_json_value(key, value):
                    continue
                fixed[key] = self.__fix_json(value)
        elif isinstance(obj, list):
            fixed = []
            for value in obj:
                fixed.append(self.__fix_json(value))
        elif isinstance(obj, float):
            # force floats to int, if they are integers
            # (prevent INTEGER_WRITTEN_AS_FLOAT validator warnings)
            if int(obj) == obj:
                return int(obj)
        return fixed

    def __should_include_json_value(self, key, value):
        allowed_empty_collections = ["KHR_materials_unlit"]

        if value is None:
            return False
        elif self.__is_empty_collection(value) and key not in allowed_empty_collections:
            return False
        return True


    def __is_empty_collection(self, value):
        return (isinstance(value, dict) or isinstance(value, list)) and len(value) == 0

    def execute(self, context):
        if bpy.data.filepath == '':
            self.report({'ERROR'}, 'Save project before exporting')
            return {'CANCELLED'}

        filepath = bpy.data.filepath.replace('.blend', '')
        filename_ext = '.glb'

        export_settings = {}
        export_settings['timestamp'] = datetime.datetime.now()
        export_settings['gltf_filepath'] = bpy.path.ensure_ext(filepath, filename_ext)

        if os.path.exists(export_settings['gltf_filepath']):
            os.remove(export_settings['gltf_filepath'])

        export_settings['gltf_filedirectory'] = os.path.dirname(
            export_settings['gltf_filepath']) + '/'
        export_settings['gltf_format'] = 'GLB'
        export_settings['gltf_image_format'] = 'NAME'
        export_settings['gltf_copyright'] = ''
        export_settings['gltf_texcoords'] = True
        export_settings['gltf_normals'] = True
        export_settings['gltf_tangents'] = False
        export_settings['gltf_draco_mesh_compression'] = False
        export_settings['gltf_materials'] = True
        export_settings['gltf_colors'] = True
        export_settings['gltf_cameras'] = False
        export_settings['gltf_selected'] = self.selected
        export_settings['gltf_layers'] = True
        export_settings['gltf_extras'] = False
        export_settings['gltf_yup'] = True
        export_settings['gltf_apply'] = False
        export_settings['gltf_current_frame'] = False
        export_settings['gltf_animations'] = False
        export_settings['gltf_frame_range'] = False
        export_settings['gltf_move_keyframes'] = False
        export_settings['gltf_force_sampling'] = False
        export_settings['gltf_skins'] = False
        export_settings['gltf_all_vertex_influences'] = False
        export_settings['gltf_frame_step'] = 1
        export_settings['gltf_morph'] = False
        export_settings['gltf_morph_normal'] = False
        export_settings['gltf_morph_tangent'] = False
        export_settings['gltf_lights'] = False
        export_settings['gltf_displacement'] = False
        export_settings['gltf_binary'] = bytearray()
        export_settings['gltf_binaryfilename'] = os.path.splitext(
            os.path.basename(bpy.path.ensure_ext(filepath, filename_ext)))[0] + '.bin'

        # TODO: In most recent version this function will return active_scene
        # as the first value for a total of 3 return values
        scenes, _animations = gltf2_blender_gather.gather_gltf2(export_settings)

        # Modify scene here

        exporter = GlTF2Exporter(export_settings['gltf_copyright'])
        exporter.add_scene(scenes[0], True)
        buffer = exporter.finalize_buffer(export_settings['gltf_filedirectory'], is_glb=True)
        exporter.finalize_images(export_settings['gltf_filedirectory'])

        gltf_json = self.__fix_json(exporter.glTF.to_dict())

        extension_name = bpy.hubs_config["gltfExtensionName"]
        gltf_json['extensionsRequired'].remove(extension_name)

        if not gltf_json['extensionsRequired']:
            del gltf_json['extensionsRequired']

        if 'extensions' not in gltf_json:
            gltf_json['extensions'] = {}

        gltf_json['extensions'][extension_name] = {
            "version": bpy.hubs_config["gltfExtensionVersion"]
        }

        gltf2_io_export.save_gltf(
            gltf_json,
            export_settings,
            gltf2_blender_json.BlenderJSONEncoder,
            buffer
        )

        self.report({'INFO'}, 'Project saved to \"%s\"' % (export_settings['gltf_filepath']))

        return {'FINISHED'}

original_gather_extensions = gltf2_blender_gather_nodes.__gather_extensions

def __to_json_compatible(value):
    """Make a value (usually a custom property) compatible with json"""

    if isinstance(value, bpy.types.ID):
        return value

    elif isinstance(value, str):
        return value

    elif isinstance(value, (int, float)):
        return value

    # for list classes
    elif isinstance(value, list):
        value = list(value)
        # make sure contents are json-compatible too
        for index in range(len(value)):
            value[index] = __to_json_compatible(value[index])
        return value

    # for IDPropertyArray classes
    elif hasattr(value, "to_list"):
        value = value.to_list()
        return value

    elif hasattr(value, "to_dict"):
        value = value.to_dict()
        if gltf2_blender_json.is_json_convertible(value):
            return value

    return None

def patched_gather_extensions(blender_object, export_settings):
    extensions = original_gather_extensions(blender_object, export_settings)

    component_list = blender_object.hubs_component_list

    if component_list.items:
        extension_name = bpy.hubs_config["gltfExtensionName"]
        component_data = {}

        for component_item in component_list.items:
            component_name = component_item.name
            component_data[component_name] = {}
            component_definition = bpy.hubs_config['components'][component_name]
            component_class = bpy.registered_hubs_components[component_name]
            component_class_name = component_class.__name__
            component = getattr(blender_object, component_class_name)

            for property_name, _property_definition in component_definition['properties'].items():
                component_data[component_name][property_name] = __to_json_compatible(
                    getattr(component, property_name)
                )

        if extensions is None:
            extensions = {}

        extensions[extension_name] = gltf2_io_extensions.Extension(
            name=extension_name,
            extension=component_data,
            required=False
        )

    return extensions if extensions else None

@persistent
def load_handler(_dummy):
    bpy.context.scene.hubs_settings.reload_config()

def register():
    bpy.utils.register_class(HubsSettings)
    bpy.utils.register_class(HubsComponentName)
    bpy.utils.register_class(HubsComponentList)
    bpy.utils.register_class(AddHubsComponentMenu)
    bpy.types.Scene.hubs_settings = PointerProperty(type=HubsSettings)
    bpy.types.Object.hubs_component_list = PointerProperty(type=HubsComponentList)
    bpy.utils.register_class(HubsSettingsPanel)
    bpy.utils.register_class(HubsObjectPanel)
    bpy.utils.register_class(ReloadHubsConfig)
    bpy.utils.register_class(AddHubsComponent)
    bpy.utils.register_class(RemoveHubsComponent)
    bpy.utils.register_class(ExportHubsGLTF)
    bpy.app.handlers.load_post.append(load_handler)
    gltf2_blender_gather_nodes.__gather_extensions = patched_gather_extensions

def unregister():
    bpy.utils.unregister_class(ReloadHubsConfig)
    bpy.utils.unregister_class(HubsObjectPanel)
    bpy.utils.unregister_class(HubsSettingsPanel)
    bpy.utils.unregister_class(HubsSettings)
    bpy.utils.unregister_class(AddHubsComponentMenu)
    bpy.utils.unregister_class(HubsComponentName)
    bpy.utils.unregister_class(HubsComponentList)
    bpy.utils.unregister_class(AddHubsComponent)
    bpy.utils.unregister_class(RemoveHubsComponent)
    bpy.utils.unregister_class(ExportHubsGLTF)
    del bpy.types.Scene.hubs_settings
    del bpy.types.Object.hubs_component_list
    bpy.hubs_config = None
    bpy.registered_hubs_components = {}
    gltf2_blender_gather_nodes.__gather_extensions = original_gather_extensions

if __name__ == "__main__":
    register()
