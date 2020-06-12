import os
import json
import bpy
import pathlib

from bpy.props import StringProperty, PointerProperty
from bpy.types import PropertyGroup, AddonPreferences
import pathlib
import os
from . import components
from .operators import ReloadHubsConfig

# Get the path to the default config file
main_dir = pathlib.Path(os.path.dirname(__file__)).resolve()
default_config_path = os.path.join(main_dir, 'default-config.json')

def get_component_class_name(component_name):
    return "hubs_component_%s" % component_name.replace('-', '_')

hubs_context = None
def reload_context(context=bpy.context):
    config_path = context.preferences.addons[__package__].preferences.config_path
    print("Reloading context")
    global hubs_context

    if os.path.splitext(config_path)[1] == '.json':
        with open(bpy.path.abspath(config_path)) as config_file:
            hubs_config = json.load(config_file)
    else:
        hubs_config = None
        print('Config must be a .json file!')

    if hubs_context:
        unregister_components()

    hubs_context = {
        'registered_hubs_components': {},
        'registered_classes': {},
        'hubs_config': hubs_config
    }

    register_components()

def unregister_components():
    try:
        if 'registered_hubs_components' in hubs_context:
            for component_name, component_class in hubs_context['registered_hubs_components'].items():
                component_class_name = get_component_class_name(component_name)
                if hasattr(bpy.types.Object, component_class_name):
                    delattr(bpy.types.Object, component_class_name)
                if hasattr(bpy.types.Material, component_class_name):
                    delattr(bpy.types.Material, component_class_name)
                if hasattr(bpy.types.Bone, component_class_name):
                    delattr(bpy.types.Bone, component_class_name)
                if hasattr(bpy.types.EditBone, component_class_name):
                    delattr(bpy.types.EditBone, component_class_name)

        if 'registered_hubs_classes' in hubs_context:
            for class_name, registered_class in hubs_context['registered_hubs_classes']:
                bpy.utils.unregister_class(registered_class)


    except UnboundLocalError:
        pass

    if 'registered_hubs_components' in hubs_context:
        hubs_context['registered_hubs_components'] = {}

    if 'registered_hubs_classes' in hubs_context:
        hubs_context['registered_hubs_classes'] = {}

def register_components():
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
            setattr(
                bpy.types.Bone,
                get_component_class_name(component_name),
                PointerProperty(type=component_class)
            )
            setattr(
                bpy.types.EditBone,
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


def config_updated(_self, context):
    reload_context(context)

class HubsAddonPreferences(AddonPreferences):
    bl_idname = __package__

    config_path: StringProperty(
        name="Component Config",
        default=default_config_path,
        subtype='FILE_PATH',
        update=config_updated
    )

    def draw(self, context):
        layout = self.layout.row()
        layout.prop(self, "config_path")
        layout.operator(ReloadHubsConfig.bl_idname, text="", icon="FILE_REFRESH")

def register():
    bpy.utils.register_class(HubsAddonPreferences)
    reload_context()

def unregister():
    bpy.utils.unregister_class(HubsAddonPreferences)
    global hubs_context
    if hubs_context:
        unregister_components()
    del hubs_context
