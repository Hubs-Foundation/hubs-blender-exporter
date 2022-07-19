import bpy
import bpy_types
from bpy.types import (Gizmo, GizmoGroup)
from bpy.props import (IntProperty)
from .components_registry import get_component_by_name
from bpy.app.handlers import persistent
from math import radians
from mathutils import Matrix


def gizmo_update(obj, gizmo):
    gizmo.matrix_basis = obj.matrix_world.normalized()


def bone_matrix_world(ob, bone, scaleOverride=None):
    loc, rot, scale = bone.matrix.to_4x4().decompose()
    # Account for bones using Y up
    rot_offset = Matrix.Rotation(radians(-90), 4, 'X').to_4x4()
    if scaleOverride:
        scale = scaleOverride
    else:
        scale = scale.xzy
    final_loc = ob.matrix_world @ Matrix.Translation(loc)
    final_rot = rot.normalized().to_matrix().to_4x4() @ rot_offset
    final_scale = Matrix.Diagonal(scale).to_4x4()
    return final_loc @ final_rot @ final_scale


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

    def add_gizmo(self, ob, host):
        print('def add_gizmo')
        for component_item in host.hubs_component_list.items:
            print('component_item:', component_item)
            component_name = component_item.name
            component_class = get_component_by_name(component_name)
            print('component_name:', component_name)
            print('component_class:', component_class)
            if not component_class:
                continue
            gizmo = component_class.create_gizmo(host, self)
            print('gizmo:', gizmo)
            if gizmo:
                if not component_name in self.widgets:
                    print('add component to widgets')
                    self.widgets[component_name] = {}

                host_key = ob.name+host.name
                print('host_key:', host_key)
                if host_key not in self.widgets[component_name]:
                    print('creating new widget')
                    self.widgets[component_name][host_key] = {
                        'ob_name': ob.name,
                        'host_name': host.name,
                        'host_type': type(host),
                        'gizmo': gizmo
                        }
                    print('widget:', self.widgets[component_name][host_key])

    def setup(self, context):
        self.widgets = {}

        for ob in bpy.data.objects:
            self.add_gizmo(ob, ob)
            if ob.type == 'ARMATURE':
                for bone in ob.data.bones:
                    self.add_gizmo(ob, bone)
                for edit_bone in ob.data.edit_bones:
                    self.add_gizmo(ob, edit_bone)

        self.refresh(context)

    def remove_gizmo(self, component_name, host_key):
        print('def remove_gizmo')
        print('component_name:', component_name)
        print('host_key:', host_key)
        gizmo = self.widgets[component_name][host_key]['gizmo']
        if gizmo:
            self.gizmos.remove(gizmo)
        del self.widgets[component_name][host_key]

    def update_gizmo(self, component_name, ob, bone, target, gizmo):
        print('def update_gizmo')
        component_class = get_component_by_name(component_name)
        component_class.update_gizmo(ob, bone, target, gizmo)

    def update_object_gizmo(self, component_name, ob, gizmo):
        print('update_object_gizmo')
        if component_name not in ob.hubs_component_list.items:
            self.remove_gizmo(component_name, ob.name+ob.name)
        else:
            self.update_gizmo(component_name, ob, None, ob, gizmo)

    def update_bone_gizmo(self, component_name, ob, bone, pose_bone, gizmo):
        print('def update_bone_gizmo')
        if component_name not in bone.hubs_component_list.items:
            self.remove_gizmo(component_name, ob.name+bone.name)
        else:
            self.update_gizmo(component_name, ob, pose_bone, bone, gizmo)

    def refresh(self, context):
        print('def refresh')
        for component_name in self.widgets:
            print('component_name:', component_name)
            components_widgets = self.widgets[component_name].copy()
            for widget in components_widgets.values():
                print('widget:', widget)
                if widget['gizmo'] and widget['gizmo'] in self.gizmos.values():
                    found = False
                    for ob in bpy.data.objects:
                        print('ob:', ob)
                        if ob.name != widget['ob_name']:
                            continue

                        print('ob.type:', ob.type)
                        if ob.type == 'ARMATURE':
                            # https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones
                            print('context.mode:', context.mode)
                            if ob.mode == 'EDIT':
                                if widget['host_name'] in ob.data.edit_bones:
                                    bone = ob.data.edit_bones[widget['host_name']]
                                    self.update_bone_gizmo(
                                        component_name, ob, bone, bone, widget['gizmo'])
                                    found = True
                                    break
                            else:
                                if widget['host_name'] in ob.data.bones:
                                    bone = ob.data.bones[widget['host_name']]
                                    pose_bone = ob.pose.bones[widget['host_name']]
                                    self.update_bone_gizmo(
                                        component_name, ob, bone, pose_bone, widget['gizmo'])
                                    found = True
                                    break

                        if widget['host_type'] == bpy_types.Object:
                            self.update_object_gizmo(
                                component_name, ob, widget['gizmo'])
                            found = True
                            break

                    if not found:
                        print('not found, removing gizmo')
                        self.gizmos.remove(widget['gizmo'])


global objects_count
ob_handle = object()
bone_handle = object()
edit_bone_handle = object()

ob_subscribe_to = (bpy.types.Object, "name")
bone_subscribe_to = (bpy.types.Bone, "name")
edit_bone_subscribe_to = (bpy.types.EditBone, "name")

def msgbus_callback(*args):
    update_gizmos()


@persistent
def undo_post(dummy):
    update_gizmos()


@persistent
def redo_post(dummy):
    update_gizmos()


@persistent
def depsgraph_update_post(dummy):
    global objects_count
    if bpy.context.mode == 'OBJECT':
        if len(bpy.data.objects) != objects_count:
            update_gizmos()
        objects_count = len(bpy.data.objects)
    elif bpy.context.mode == 'EDIT_ARMATURE':
        for ob in bpy.context.objects_in_mode:
            if len(ob.data.edit_bones) != ob.data.hubs_old_bones_length:
                update_gizmos()
            ob.data.hubs_old_bones_length = len(ob.data.edit_bones)


@persistent
def load_post(dummy):
    global objects_count
    objects_count = len(bpy.data.objects)
    update_gizmos()
    bpy.msgbus.subscribe_rna(
        key=ob_subscribe_to,
        owner=ob_handle,
        args=(bpy.context,),
        notify=msgbus_callback,
    )
    bpy.msgbus.subscribe_rna(
        key=bone_subscribe_to,
        owner=bone_handle,
        args=(bpy.context,),
        notify=msgbus_callback,
    )
    bpy.msgbus.subscribe_rna(
        key=edit_bone_subscribe_to,
        owner=edit_bone_handle,
        args=(bpy.context,),
        notify=msgbus_callback,
    )


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
        if not undo_post in bpy.app.handlers.undo_post:
            bpy.app.handlers.undo_post.append(
                undo_post)
        if not redo_post in bpy.app.handlers.redo_post:
            bpy.app.handlers.redo_post.append(
                redo_post)

        bpy.types.Armature.hubs_old_bones_length = IntProperty(options={'HIDDEN', 'SKIP_SAVE'})

        register_gizmo_classes()

        bpy.msgbus.subscribe_rna(
            key=ob_subscribe_to,
            owner=ob_handle,
            args=(bpy.context,),
            notify=msgbus_callback,
        )
        bpy.msgbus.subscribe_rna(
            key=bone_subscribe_to,
            owner=bone_handle,
            args=(bpy.context,),
            notify=msgbus_callback,
        )
        bpy.msgbus.subscribe_rna(
            key=edit_bone_subscribe_to,
            owner=edit_bone_handle,
            args=(bpy.context,),
            notify=msgbus_callback,
        )


    def unregister():
        if load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post)
        if depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(
                depsgraph_update_post)
        if undo_post in bpy.app.handlers.undo_post:
            bpy.app.handlers.undo_post.remove(
                undo_post)
        if redo_post in bpy.app.handlers.redo_post:
            bpy.app.handlers.redo_post.remove(
                redo_post)

        unregister_gizmo_classes()

        del bpy.types.Armature.hubs_old_bones_length

        bpy.msgbus.clear_by_owner(ob_handle)
        bpy.msgbus.clear_by_owner(bone_handle)
        bpy.msgbus.clear_by_owner(edit_bone_handle)

    return register, unregister


register, unregister = register_functions()
