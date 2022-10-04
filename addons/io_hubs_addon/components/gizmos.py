import bpy
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

    def add_gizmo(self, ob, host, host_type):
        for component_item in host.hubs_component_list.items:
            component_name = component_item.name
            component_class = get_component_by_name(component_name)
            if not component_class:
                continue
            gizmo = component_class.create_gizmo(host, self)
            if gizmo:
                if not component_name in self.widgets:
                    self.widgets[component_name] = {}

                host_key = ob.name+host.name
                if host_key not in self.widgets[component_name]:
                    self.widgets[component_name][host_key] = {
                        'ob': ob,
                        'host_name': host.name,
                        'host_type': host_type,
                        'gizmo': gizmo
                        }

                    if host_type == 'OBJECT':
                        owner = object()
                        msgbus_owners.append(owner)
                        subscribe_to = host.path_resolve("name", False)
                        bpy.msgbus.subscribe_rna(
                            key=subscribe_to,
                            owner=owner,
                            args=(bpy.context,),
                            notify=msgbus_callback,
                        )

    def setup(self, context):
        self.widgets = {}

        for ob in context.scene.objects:
            self.add_gizmo(ob, ob, 'OBJECT')
            if ob.type == 'ARMATURE':
                if ob.mode == 'EDIT':
                    for edit_bone in ob.data.edit_bones:
                        self.add_gizmo(ob, edit_bone, 'BONE')
                else:
                    for bone in ob.data.bones:
                        self.add_gizmo(ob, bone, 'BONE')

        if not self.widgets:
            bpy.app.timers.register(unregister_gizmo_system)
            return

        self.refresh(context)

    def update_gizmo(self, component_name, ob, bone, target, gizmo):
        component_class = get_component_by_name(component_name)
        component_class.update_gizmo(ob, bone, target, gizmo)

    def update_object_gizmo(self, component_name, ob, gizmo):
        self.update_gizmo(component_name, ob, None, ob, gizmo)

    def update_bone_gizmo(self, component_name, ob, bone, pose_bone, gizmo):
        self.update_gizmo(component_name, ob, pose_bone, bone, gizmo)

    def refresh(self, context):
        for component_name in self.widgets:
            component_widgets = self.widgets[component_name].copy()
            for widget in component_widgets.values():
                gizmo = widget['gizmo']
                ob = widget['ob']
                host_name = widget['host_name']

                try:
                    if widget['host_type'] == 'BONE':
                        # https://docs.blender.org/api/current/info_gotcha.html#editbones-posebones-bone-bones
                        if ob.mode == 'EDIT':
                            edit_bone = ob.data.edit_bones[host_name]
                            self.update_bone_gizmo(
                                        component_name, ob, edit_bone, edit_bone, gizmo)
                        else:
                            bone = ob.data.bones[host_name]
                            pose_bone = ob.pose.bones[host_name]
                            self.update_bone_gizmo(
                                        component_name, ob, bone, pose_bone, gizmo)
                    else:
                        self.update_object_gizmo(
                                component_name, ob, gizmo)

                except ReferenceError:
                    # This shouldn't happen, but if objects and widgets have gotten out of sync refresh the whole system
                    bpy.app.timers.register(update_gizmos)
                    return


objects_count = -1
gizmo_system_registered = False
msgbus_owners = []

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
    unregister_gizmo_system()
    register_gizmo_system()


def register_gizmo_system():
    global objects_count
    global gizmo_system_registered
    global msgbus_owners

    try:
        objects_count = len(bpy.data.objects)
    except AttributeError:
        pass

    if not depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(
            depsgraph_update_post)
    if not undo_post in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.append(
            undo_post)
    if not redo_post in bpy.app.handlers.redo_post:
        bpy.app.handlers.redo_post.append(
            redo_post)

    for bonetype in [bpy.types.Bone, bpy.types.EditBone]:
        owner = object()
        msgbus_owners.append(owner)
        bpy.msgbus.subscribe_rna(
            key=(bonetype, "name"),
            owner=owner,
            args=(bpy.context,),
            notify=msgbus_callback,
        )


    register_gizmos()
    gizmo_system_registered = True

def register_gizmos():
    try:
        bpy.utils.register_class(CustomModelGizmo)
        bpy.utils.register_class(HubsGizmoGroup)
    except:
        pass

def unregister_gizmo_system():
    global objects_count
    global gizmo_system_registered
    global msgbus_owners

    if depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(
            depsgraph_update_post)
    if undo_post in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.remove(
            undo_post)
    if redo_post in bpy.app.handlers.redo_post:
        bpy.app.handlers.redo_post.remove(
            redo_post)

    for owner in msgbus_owners:
        bpy.msgbus.clear_by_owner(owner)
    msgbus_owners.clear()

    unregister_gizmos()
    gizmo_system_registered = False
    objects_count = -1

def unregister_gizmos():
    try:
        bpy.utils.unregister_class(HubsGizmoGroup)
        bpy.utils.unregister_class(CustomModelGizmo)
    except:
        pass

def update_gizmos():
    global gizmo_system_registered
    unregister_gizmos()
    register_gizmos() if gizmo_system_registered else register_gizmo_system()

def register_functions():
    def register():
        if not load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_post)

        bpy.types.Armature.hubs_old_bones_length = IntProperty(options={'HIDDEN', 'SKIP_SAVE'})

        register_gizmo_system()

    def unregister():
        if load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post)


        unregister_gizmo_system()

        del bpy.types.Armature.hubs_old_bones_length

    return register, unregister


register, unregister = register_functions()
