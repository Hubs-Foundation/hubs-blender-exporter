import os
import json
import bpy
from bpy.props import StringProperty, PointerProperty
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent
from . import components

# Get the path to the default config file
paths = bpy.utils.script_paths("addons")

default_config_filename = 'default-config.json'
default_config_path = default_config_filename

for path in paths:
    default_config_path = os.path.join(path, "io_scene_mozcomponents", default_config_filename)
    if os.path.exists(default_config_path):
        break

def get_component_class_name(component_name):
    return "moz_component_%s" % component_name.replace('-', '_')

def reload_context(config_path):
    global mozcomponents_context

    if os.path.splitext(config_path)[1] == '.json':
        with open(bpy.path.abspath(config_path)) as config_file:
            mozcomponents_config = json.load(config_file)
    else:
        mozcomponents_config = None
        print('Config must be a .json file!')

    if 'mozcomponents_context' in globals():
        unregister_components()

    mozcomponents_context = {
        'registered_moz_components': {},
        'registered_classes': {},
        'mozcomponents_config': mozcomponents_config
    }

    register_components()

def unregister_components():
    global mozcomponents_context

    try:
        if 'registered_moz_components' in mozcomponents_context:
            for component_name, component_class in mozcomponents_context['registered_moz_components'].items():
                component_class_name = get_component_class_name(component_name)
                if hasattr(bpy.types.Object, component_class_name):
                    delattr(bpy.types.Object, component_class_name)

        if 'registered_moz_classes' in mozcomponents_context:
            for class_name, registered_class in mozcomponents_context['registered_moz_classes']:
                bpy.utils.unregister_class(registered_class)


    except UnboundLocalError:
        pass

    if 'registered_moz_components' in mozcomponents_context:
        mozcomponents_context['registered_moz_components'] = {}

    if 'registered_moz_classes' in mozcomponents_context:
        mozcomponents_context['registered_moz_classes'] = {}

def register_components():
    global mozcomponents_context

    for component_name, component_definition in mozcomponents_context['mozcomponents_config']['components'].items():
        class_name = "moz_component_%s" % component_name.replace('-', '_')

        component_class = components.define_class(
            class_name,
            component_definition,
            mozcomponents_context
        )

        if 'scene' in component_definition and component_definition['scene']:
            setattr(
                bpy.types.Scene,
                get_component_class_name(component_name),
                PointerProperty(type=component_class)
            )

        if not 'node' in component_definition or component_definition['node']:
            setattr(
                bpy.types.Object,
                get_component_class_name(component_name),
                PointerProperty(type=component_class)
            )

        if 'material' in component_definition and component_definition['material']:
            setattr(
                bpy.types.Material,
                get_component_class_name(component_name),
                PointerProperty(type=component_class)
            )

        mozcomponents_context['registered_moz_components'][component_name] = component_class

@persistent
def load_handler(_dummy):
    reload_context(bpy.context.scene.mozcomponents_settings.config_path)

def config_updated(self, _context):
    load_handler(self)

class MozComponentsSettings(PropertyGroup):
    config_path: StringProperty(
        name="config_path",
        description="Path to the config file",
        default=default_config_path,
        options={'HIDDEN'},
        maxlen=1024,
        subtype='FILE_PATH',
        update=config_updated
    )

    @property
    def mozcomponents_config(self):
        global mozcomponents_context
        return mozcomponents_context['mozcomponents_config']

    @property
    def registered_moz_components(self):
        return mozcomponents_context['registered_moz_components']

    @property
    def registered_moz_classes(self):
        return mozcomponents_context['registered_moz_classes']

    def reload_config(self):
        reload_context(self.config_path)

def register():
    bpy.utils.register_class(MozComponentsSettings)
    bpy.types.Scene.mozcomponents_settings = PointerProperty(type=MozComponentsSettings)
    bpy.app.handlers.load_post.append(load_handler)
    reload_context(default_config_path)

def unregister():
    global mozcomponents_context
    del mozcomponents_context
    bpy.utils.unregister_class(MozComponentsSettings)
    del bpy.types.Scene.mozcomponents_settings
    bpy.app.handlers.load_post.remove(load_handler)
