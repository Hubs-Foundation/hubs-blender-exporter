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
    default_config_path = os.path.join(path, "io_scene_hubs", default_config_filename)
    if os.path.exists(default_config_path):
        break

def get_component_class_name(component_name):
    return "hubs_component_%s" % component_name.replace('-', '_')

def reload_context(config_path):
    global hubs_context

    if os.path.splitext(config_path)[1] == '.json':
        with open(bpy.path.abspath(config_path)) as config_file:
            hubs_config = json.load(config_file)
    else:
        hubs_config = None
        print('Config must be a .json file!')

    if 'hubs_context' in globals():
        unregister_components()

    hubs_context = {
        'registered_hubs_components': {},
        'registered_classes': {},
        'hubs_config': hubs_config
    }

    register_components()

def unregister_components():
    global hubs_context

    try:
        if hubs_context['registered_hubs_components']:
            for component_name, component_class in hubs_context['registered_hubs_components'].items():
                component_class_name = get_component_class_name(component_name)
                if hasattr(bpy.types.Object, component_class_name):
                    delattr(bpy.types.Object, component_class_name)

        if hubs_context['registered_hubs_classes']:
            for class_name, registered_class in hubs_context['registered_hubs_classes']:
                bpy.utils.unregister_class(registered_class)


    except UnboundLocalError:
        pass

    if 'registered_hubs_components' in hubs_context:
        hubs_context['registered_hubs_components'] = {}

    if 'registered_hubs_classes' in hubs_context:
        hubs_context['registered_hubs_classes'] = {}

def register_components():
    global hubs_context

    for component_name, component_definition in hubs_context['hubs_config']['components'].items():
        class_name = "hubs_component_%s" % component_name.replace('-', '_')

        component_class = components.define_class(
            class_name,
            component_definition,
            hubs_context
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

        hubs_context['registered_hubs_components'][component_name] = component_class

@persistent
def load_handler(_dummy):
    reload_context(bpy.context.scene.hubs_settings.config_path)

def config_updated(self, _context):
    load_handler(self)

class HubsSettings(PropertyGroup):
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
    def hubs_config(self):
        global hubs_context
        return hubs_context['hubs_config']

    @property
    def registered_hubs_components(self):
        return hubs_context['registered_hubs_components']

    @property
    def registered_hubs_classes(self):
        return hubs_context['registered_hubs_classes']

    def reload_config(self):
        reload_context(self.config_path)

def register():
    bpy.utils.register_class(HubsSettings)
    bpy.types.Scene.hubs_settings = PointerProperty(type=HubsSettings)
    bpy.app.handlers.load_post.append(load_handler)
    reload_context(default_config_path)

def unregister():
    global hubs_context
    del hubs_context
    bpy.utils.unregister_class(HubsSettings)
    del bpy.types.Scene.hubs_settings
    bpy.app.handlers.load_post.remove(load_handler)
