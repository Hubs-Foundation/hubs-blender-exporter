import bpy
from bpy.types import (Gizmo, GizmoGroup)
from bpy.props import BoolProperty
from .components_registry import get_component_by_name
from bpy.app.handlers import persistent


def gizmo_update(obj, gizmo):
    gizmo.matrix_basis = obj.matrix_world.normalized()


class CustomModelGizmo(Gizmo):
    """Generic gizmo to render all Hubs custom gizmos"""
    bl_idname = "GIZMO_GT_hba_gizmo"

    __slots__ = (
        "object",
        "hubs_gizmo_shape",
        "custom_shape",
    )

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def setup(self):
        if hasattr(self, "hubs_gizmo_shape"):
            self.custom_shape = self.new_custom_shape(
                'TRIS', self.hubs_gizmo_shape)

    def invoke(self, context, event):
        if hasattr(self, "object") and context.mode == 'OBJECT':
            if not event.shift:
                bpy.ops.object.select_all(action='DESELECT')
            self.object.select_set(True)
            bpy.context.view_layer.objects.active = self.object

        return {'RUNNING_MODAL'}

    def modal(self, context, event, tweak):
        return {'RUNNING_MODAL'}


class HubsGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_hba_gizmo_group"
    bl_label = "Hubs gizmo group"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL', 'SELECT'}

    def add_gizmo(self, ob, name):
        for component_item in ob.hubs_component_list.items:
            component_name = component_item.name
            component_class = get_component_by_name(component_name)
            if not component_class:
                continue
            gizmo = component_class.create_gizmo(ob, self)
            if gizmo:
                if not component_name in self.widgets:
                    self.widgets[component_name] = {}
                if name not in self.widgets[component_name]:
                    self.widgets[component_name][name] = gizmo

    def setup(self, context):
        self.widgets = {}

        for ob in bpy.data.objects:
            self.add_gizmo(ob, ob.name)
            if ob.type == 'ARMATURE':
                for bone in ob.data.bones:
                    self.add_gizmo(bone, bone.name)
                for edit_bone in ob.data.edit_bones:
                    self.add_gizmo(edit_bone, edit_bone.name)

        self.refresh(context)

    def remove_gizmo(self, component_name, ob_name):
        gizmo = self.widgets[component_name][ob_name]
        if gizmo:
            self.gizmos.remove(gizmo)
        del self.widgets[component_name][ob_name]

    def update_gizmo(self, component_name, ob, bone, target, gizmo):
        component_class = get_component_by_name(component_name)
        component_class.update_gizmo(ob, bone, target, gizmo)

    def update_object_gizmo(self, component_name, ob, gizmo):
        if component_name not in ob.hubs_component_list.items:
            self.remove_gizmo(component_name, ob.name)
        else:
            self.update_gizmo(component_name, ob, None, ob, gizmo)

    def update_bone_gizmo(self, component_name, ob, bone, pose_bone, gizmo):
        if component_name not in bone.hubs_component_list.items:
            self.remove_gizmo(component_name, bone.name)
        else:
            self.update_gizmo(component_name, ob, pose_bone, bone, gizmo)

    def refresh(self, context):
        for component_name in self.widgets:
            components_widgets = self.widgets[component_name].copy()
            for name in components_widgets:
                gizmo = components_widgets[name]
                if gizmo and gizmo in self.gizmos.values():
                    found = False
                    for ob in bpy.data.objects:
                        if ob.type == 'ARMATURE':
                            # https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones
                            if context.mode == 'EDIT_ARMATURE':
                                if name in ob.data.edit_bones:
                                    bone = ob.data.edit_bones[name]
                                    self.update_bone_gizmo(
                                        component_name, ob, bone, bone, gizmo)
                                    found = True
                            else:
                                if name in ob.data.bones:
                                    bone = ob.data.bones[name]
                                    pose_bone = ob.pose.bones[name]
                                    self.update_bone_gizmo(
                                        component_name, ob, bone, pose_bone, gizmo)
                                    found = True

                        if name == ob.name:
                            self.update_object_gizmo(
                                component_name, ob, gizmo)
                            found = True

                    if not found:
                        self.gizmos.remove(gizmo)


global objects_count


@persistent
def undo_post(dummy):
    update_gizmos()


@persistent
def redo_post(dummy):
    update_gizmos()


@persistent
def depsgraph_update_post(dummy):
    global objects_count
    if len(bpy.data.objects) != objects_count:
        update_gizmos()
    objects_count = len(bpy.data.objects)


@persistent
def load_post(dummy):
    global objects_count
    objects_count = len(bpy.data.objects)
    update_gizmos()


def register_gizmo_classes():
    bpy.utils.register_class(CustomModelGizmo)
    bpy.utils.register_class(HubsGizmoGroup)


def unregister_gizmo_classes():
    bpy.utils.unregister_class(HubsGizmoGroup)
    bpy.utils.unregister_class(CustomModelGizmo)


def update_gizmos():
    try:
        unregister_gizmo_classes()
    except:
        pass

    register_gizmo_classes()


def register_functions():
    def register():
        if not load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_post)
        if not depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(
                depsgraph_update_post)
        register_gizmo_classes()

    def unregister():
        if load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post)
        if depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(
                depsgraph_update_post)
        unregister_gizmo_classes()

    return register, unregister


register, unregister = register_functions()
