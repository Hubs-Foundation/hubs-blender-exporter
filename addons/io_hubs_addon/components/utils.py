from . import components_registry
from .gizmos import update_gizmos


def add_component(obj, component_id):
    component_item = obj.hubs_component_list.items.add()
    component_item.name = component_id

    component_class = components_registry.get_component_by_name(component_id)
    if component_class:
        update_gizmos()
        for dep_id in component_class.get_deps():
            dep_class = components_registry.get_component_by_id(dep_id)
            if dep_class:
                dep_exists = obj.hubs_component_list.items.find(dep_id) > -1
                if not dep_exists:
                    add_component(obj, dep_id)
            else:
                print("Dependecy '%s' from module '%s' not registered" %
                      (dep_id, component_id))


def remove_component(obj, component_id):
    component_items = obj.hubs_component_list.items
    component_items.remove(component_items.find(component_id))
    component_class = components_registry.get_component_by_id(component_id)
    del obj[component_class.get_name()]

    component_class = components_registry.get_component_by_name(component_id)
    if component_class:
        update_gizmos()
        for dep_id in component_class.get_deps():
            dep_class = components_registry.get_component_by_id(dep_id)
            dep_id = dep_class.get_id()
            if dep_class:
                if not is_dep_required(obj, component_id, dep_id):
                    remove_component(obj, dep_id)
            else:
                print("Dependecy '%s' from module '%s' not registered" %
                      (dep_id, component_id))


def has_component(obj, component_id):
    component_items = obj.hubs_component_list.items
    return component_id in component_items


def has_components(obj, component_ids):
    component_items = obj.hubs_component_list.items
    for name in component_ids:
        if name not in component_items:
            return False
    return True


def is_dep_required(obj, component_id, dep_id):
    '''Checks if there is any other component that requires this dependency'''
    is_required = False
    items = obj.hubs_component_list.items
    for cmp in items:
        if cmp.name != component_id:
            dep_component_class = components_registry.get_component_by_name(
                cmp.name)
            if dep_id in dep_component_class.get_deps():
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