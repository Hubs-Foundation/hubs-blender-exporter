import bpy
from .components_registry import get_component_by_name
from .gizmos import update_gizmos
from mathutils import Vector

V_S1 = Vector((1.0, 1.0, 1.0))


def add_component(obj, component_name):
    print('def add_component')
    print('obj:', obj)
    print('component_name:', component_name)
    component_item = obj.hubs_component_list.items.add()
    component_item.name = component_name

    component_class = get_component_by_name(component_name)
    print('component_class:', component_class)
    if component_class:
        update_gizmos()
        component_class.init(obj)
        for dep_name in component_class.get_deps():
            dep_class = get_component_by_name(dep_name)
            if dep_class:
                dep_exists = obj.hubs_component_list.items.find(dep_name) > -1
                if not dep_exists:
                    add_component(obj, dep_name)
            else:
                print("Dependecy '%s' from module '%s' not registered" %
                      (dep_name, component_name))


def remove_component(obj, component_name):
    component_items = obj.hubs_component_list.items
    component_items.remove(component_items.find(component_name))
    component_class = get_component_by_name(component_name)

    component_class = get_component_by_name(component_name)
    if component_class:
        del obj[component_class.get_id()]
        update_gizmos()
        for dep_name in component_class.get_deps():
            dep_class = get_component_by_name(dep_name)
            dep_name = dep_class.get_name()
            if dep_class:
                if not is_dep_required(obj, component_name, dep_name):
                    remove_component(obj, dep_name)
            else:
                print("Dependecy '%s' from module '%s' not registered" %
                      (dep_name, component_name))


def has_component(obj, component_name):
    component_items = obj.hubs_component_list.items
    return component_name in component_items


def has_components(obj, component_names):
    component_items = obj.hubs_component_list.items
    for name in component_names:
        if name not in component_items:
            return False
    return True


def is_dep_required(obj, component_name, dep_name):
    '''Checks if there is any other component that requires this dependency'''
    is_required = False
    items = obj.hubs_component_list.items
    for cmp in items:
        if cmp.name != component_name:
            dep_component_class = get_component_by_name(
                cmp.name)
            if dep_name in dep_component_class.get_deps():
                is_required = True
                break
    return is_required


def get_object_source(context, panel_type):
    if panel_type == "material":
        return context.material
    elif panel_type == "bone":
        return context.bone or context.edit_bone
    elif panel_type == "scene":
        return context.scene
    else:
        return context.object


def dash_to_title(s):
    return s.replace("-", " ").title()


def children_recurse(ob, result):
    for child in ob.children:
        result.append(child)
        children_recurse(child, result)


def children_recursive(ob):
    if bpy.app.version < (3, 0, 0):
        ret = []
        children_recurse(ob, ret)
        return ret
    else:
        return ob.children_recursive
