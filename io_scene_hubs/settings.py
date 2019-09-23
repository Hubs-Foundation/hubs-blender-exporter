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

def config_updated(self, _context):
    self.reload_config()

bpy.registered_hubs_components = {}

bpy.hubs_config = None

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
        return bpy.hubs_config

    @property
    def registered_hubs_components(self):
        return bpy.registered_hubs_components

    def unregister_compoents(self):
        try:
            for component_name, component_class in self.registered_hubs_components.items():
                delattr(bpy.types.Object, get_component_class_name(component_name))
                bpy.utils.unregister_class(component_class)
        except UnboundLocalError:
            pass

        bpy.registered_hubs_components = {}

    def register_components(self):
        for component_name, component_definition in self.hubs_config['components'].items():
            component_class = components.create_component_class(
                component_name,
                component_definition
            )
            bpy.utils.register_class(component_class)

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

            self.registered_hubs_components[component_name] = component_class

    def load_config(self):
        if not self.hubs_config:
            self.reload_config()

    def reload_config(self):
        if os.path.splitext(self.config_path)[1] == '.json':
            with open(bpy.path.abspath(self.config_path)) as config_file:
                bpy.hubs_config = json.load(config_file)
        else:
            print('Config must be a .json file!')

        self.unregister_compoents()
        self.register_components()

@persistent
def load_handler(_dummy):
    bpy.context.scene.hubs_settings.load_config()

def register():
    bpy.utils.register_class(HubsSettings)
    bpy.types.Scene.hubs_settings = PointerProperty(type=HubsSettings)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    bpy.utils.unregister_class(HubsSettings)
    del bpy.types.Scene.hubs_settings
    bpy.app.handlers.load_post.remove(load_handler)
