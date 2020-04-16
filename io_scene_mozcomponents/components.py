import bpy
from bpy.props import IntVectorProperty, BoolProperty, FloatProperty, StringProperty
from bpy.props import PointerProperty, FloatVectorProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup, Material

class StringArrayValueProperty(PropertyGroup):
    value: StringProperty(name="value", default="")

class MaterialArrayValueProperty(PropertyGroup):
    value: PointerProperty(name="value", type=Material)

class Material2DArrayValueProperty(PropertyGroup):
    value: CollectionProperty(name="value", type=MaterialArrayValueProperty)

class MozComponentName(PropertyGroup):
    name: StringProperty(name="name")

class MozComponentList(PropertyGroup):
    items: CollectionProperty(type=MozComponentName)

class MozComponentsExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Export Moz Components",
        description='Include this extension in the exported glTF file.',
        default=True
        )
    float_property: bpy.props.FloatProperty(
        name='Sample FloatProperty',
        description='This is an example of a FloatProperty used by a UserExtension.',
        default=1.0
        )

def is_scene_component(component_definition):
    return 'scene' in component_definition and component_definition['scene']

def is_node_component(component_definition):
    return not 'node' in component_definition or component_definition['node']

def is_material_component(component_definition):
    return 'material' in component_definition and component_definition['material']

def is_object_source_component(object_source, component_definition):
    if object_source == 'material':
        return is_material_component(component_definition)
    if object_source == 'scene':
        return is_scene_component(component_definition)
    return is_node_component(component_definition)

def get_object_source(context, object_source):
    if object_source == "material":
        return context.material
    elif object_source == "scene":
        return context.scene
    else:
        return context.object

def define_class(class_name, class_definition, mozcomponents_context):
    registered_classes = mozcomponents_context['registered_classes']

    if class_name in registered_classes:
        return registered_classes[class_name]

    class_property_dict = {}

    for property_name, property_definition in class_definition['properties'].items():
        property_class = define_property(class_name, property_name, property_definition, mozcomponents_context)

        if property_class:
            class_property_dict[property_name] = property_class

    class_property_dict['definition'] = class_definition

    component_class = type(class_name, (PropertyGroup,), class_property_dict)

    registered_classes[class_name] = component_class

    bpy.utils.register_class(component_class)

    return component_class

def define_type(type_name, mozcomponents_context):
    final_class_name = "mozcomponents_type_%s" % type_name.replace('-', '_')

    registered_classes = mozcomponents_context['registered_classes']

    if final_class_name in registered_classes:
        return registered_classes[final_class_name]

    mozcomponents_config = mozcomponents_context['mozcomponents_config']

    if 'types' not in mozcomponents_config:
        raise TypeError('MOZ_Components config has no types definition.')

    if type_name not in mozcomponents_config['types']:
        raise TypeError('Undefined MOZ_Components type \'%s\'' % (type_name))

    class_definition = mozcomponents_config['types'][type_name]

    return define_class(final_class_name, class_definition, mozcomponents_context)

def define_property(class_name, property_name, property_definition, mozcomponents_context):
    property_type = property_definition['type']

    if property_type == 'int':
        return IntProperty(
            name=property_name
        )
    elif property_type == 'float':
        return FloatProperty(
            name=property_name
        )
    elif property_type == 'bool':
        return BoolProperty(
            name=property_name
        )
    elif property_type == 'string':
        return StringProperty(
            name=property_name
        )
    elif property_type == 'ivec2':
        return IntVectorProperty(
            name=property_name,
            size=2
        )
    elif property_type == 'ivec3':
        return IntVectorProperty(
            name=property_name,
            size=3
        )
    elif property_type == 'ivec4':
        return IntVectorProperty(
            name=property_name,
            size=4
        )
    elif property_type == 'vec2':
        return FloatVectorProperty(
            name=property_name,
            size=2
        )
    elif property_type == 'vec3':
        return FloatVectorProperty(
            name=property_name,
            size=3
        )
    elif property_type == 'vec4':
        return FloatVectorProperty(
            name=property_name,
            size=4
        )
    elif property_type == 'color':
        return FloatVectorProperty(
            name=property_name,
            subtype='COLOR',
            default=(1.0, 1.0, 1.0, 1.0),
            size=4,
            min=0,
            max=1
        )
    elif property_type == 'material':
        return PointerProperty(name=property_name, type=Material)
    elif property_type == 'collections':
        # collections come from the object's users_collection property
        # and don't have an associated Property
        return None
    elif property_type == 'array':
        if 'arrayType' not in property_definition:
            raise TypeError('MOZ_Components array property  \'%s\' does not specify an arrayType on %s' % (
                property_name, class_name))

        array_type = property_definition['arrayType']

        property_class = define_type(array_type, mozcomponents_context)

        if not property_class:
            raise TypeError('Unsupported MOZ_Components array type \'%s\' for %s on %s' % (
                array_type, property_name, class_name))

        return CollectionProperty(
            name=property_name,
            type=property_class
        )
    else:
        property_class = define_type(property_type, mozcomponents_context)

        if not property_class:
            raise TypeError('Unsupported MOZ_Components property type \'%s\' for %s on %s' % (
                property_type, property_name, class_name))

        return PointerProperty(
            name=property_name,
            type=property_class
        )

def get_default_value(obj, path_or_value):
    if type(path_or_value) is str and path_or_value.startswith('$'):
        path_parts = path_or_value.replace('$', '').split('.')
        return get_path(obj, path_parts)
    else:
        return path_or_value

def get_path(obj, path_parts):
    if len(path_parts) == 1:
        return getattr(obj, path_parts[0])
    else:
        first, rest = path_parts[0], path_parts[1:]
        if first == '*':
            return get_wildcard(obj, rest)
        else:
            return get_path(getattr(obj, first), rest)

def get_wildcard(arr, path_parts):
    values = []
    for item in arr:
        values.append(get_path(item, path_parts))
    return values

def add_component(obj, component_name, mozcomponents_config, registered_moz_components):
    item = obj.mozcomponents_component_list.items.add()
    item.name = component_name
    component_definition = mozcomponents_config['components'][component_name]
    component_class = registered_moz_components[component_name]
    component_class_name = component_class.__name__
    component = getattr(obj, component_class_name)

    if 'properties' not in component_definition:
        raise TypeError('MOZ_Components component \'%s\' definition has no properties field.' % (
            component_name))

    for property_name, property_definition in component_definition['properties'].items():
        if "default" in property_definition:
            default_key = property_definition["default"]
            default_value = get_default_value(obj, default_key)
            property_type = property_definition['type']

            if property_type == 'array':
                arr = getattr(component, property_name)
                for value in default_value:
                    item = arr.add()
                    item.value = value
            else:
                component[property_name] = default_value

def remove_component(obj, component_name):
    items = obj.mozcomponents_component_list.items
    items.remove(items.find(component_name))

def has_component(obj, component_name):
    items = obj.mozcomponents_component_list.items
    return component_name in items

def register():
    bpy.utils.register_class(StringArrayValueProperty)
    bpy.utils.register_class(MaterialArrayValueProperty)
    bpy.utils.register_class(Material2DArrayValueProperty)
    bpy.utils.register_class(MozComponentName)
    bpy.utils.register_class(MozComponentList)
    bpy.utils.register_class(MozComponentsExtensionProperties)
    bpy.types.Object.mozcomponents_component_list = PointerProperty(type=MozComponentList)
    bpy.types.Scene.mozcomponents_component_list = PointerProperty(type=MozComponentList)
    bpy.types.Material.mozcomponents_component_list = PointerProperty(type=MozComponentList)
    bpy.types.Scene.MozComponentsExtensionProperties = PointerProperty(type=MozComponentsExtensionProperties)

def unregister():
    bpy.utils.unregister_class(StringArrayValueProperty)
    bpy.utils.unregister_class(MaterialArrayValueProperty)
    bpy.utils.unregister_class(Material2DArrayValueProperty)
    bpy.utils.unregister_class(MozComponentName)
    bpy.utils.unregister_class(MozComponentList)
    bpy.utils.unregister_class(MozComponentsExtensionProperties)
    del bpy.types.Object.mozcomponents_component_list
    del bpy.types.Scene.mozcomponents_component_list
    del bpy.types.Material.mozcomponents_component_list
    del bpy.types.Scene.MozComponentsExtensionProperties
