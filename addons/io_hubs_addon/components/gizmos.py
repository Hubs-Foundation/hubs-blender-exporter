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

    has_widgets = False
    windows_processed = 0

    def add_gizmo(self, ob, host, host_type):
        for component_item in host.hubs_component_list.items:
            component_name = component_item.name
            component_class = get_component_by_name(component_name)
            if not component_class:
                continue
            gizmo = component_class.create_gizmo(host, self)
            if gizmo:
                if component_name not in self.widgets:
                    self.widgets[component_name] = {}

                host_key = ob.name_full + host.name
                if host_key not in self.widgets[component_name]:
                    self.widgets[component_name][host_key] = {
                        'ob': ob,
                        'host_name': host.name,
                        'host_type': host_type,
                        'gizmo': gizmo
                    }

    def setup(self, context):
        # A new instance of the gizmo group is instantiated, and setup is called once for each instance, for each open window.
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

        if self.widgets:
            HubsGizmoGroup.has_widgets = True

        HubsGizmoGroup.windows_processed += 1

        if HubsGizmoGroup.windows_processed == len(context.window_manager.windows):
            if not HubsGizmoGroup.has_widgets:
                bpy.app.timers.register(unregister_gizmo_system)
                return

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
                    # This shouldn't happen, but if objects and widgets have gotten out of sync refresh the whole system.
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
    do_gizmo_update = False
    open_scenes_object_count = 0
    wm = bpy.context.window_manager
    for window in wm.windows:
        open_scenes_object_count += len(window.scene.objects)
        active_object = window.view_layer.objects.active
        if active_object:
            if active_object.type == 'ARMATURE' and active_object.mode == 'EDIT':
                edited_objects = set(window.view_layer.objects.selected)
                edited_objects.add(active_object)
                for ob in edited_objects:
                    if len(ob.data.edit_bones) != ob.data.hubs_old_bones_length:
                        do_gizmo_update = True
                        ob.data.hubs_old_bones_length = len(ob.data.edit_bones)

    if open_scenes_object_count != objects_count:
        do_gizmo_update = True

    objects_count = open_scenes_object_count

    if do_gizmo_update:
        update_gizmos()


@persistent
def load_post(dummy):
    global objects_count
    objects_count = -1
    unregister_gizmo_system()
    register_gizmo_system()


def register_gizmo_system():
    global gizmo_system_registered
    global msgbus_owners

    if undo_post not in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.append(
            undo_post)
    if redo_post not in bpy.app.handlers.redo_post:
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
        HubsGizmoGroup.has_widgets = False
        HubsGizmoGroup.windows_processed = 0
        bpy.utils.register_class(CustomModelGizmo)
        bpy.utils.register_class(HubsGizmoGroup)
    except Exception:
        pass


def unregister_gizmo_system():
    global gizmo_system_registered
    global msgbus_owners

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


def unregister_gizmos():
    try:
        bpy.utils.unregister_class(HubsGizmoGroup)
        bpy.utils.unregister_class(CustomModelGizmo)
    except Exception:
        pass


def update_gizmos():
    global gizmo_system_registered
    unregister_gizmos()
    register_gizmos() if gizmo_system_registered else register_gizmo_system()


def register_functions():
    def register():
        global objects_count
        objects_count = -1

        if load_post not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_post)
        if not depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(
                depsgraph_update_post)

        bpy.types.Armature.hubs_old_bones_length = IntProperty(
            options={'HIDDEN', 'SKIP_SAVE'})

        register_gizmo_system()

    def unregister():
        if load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post)
        if depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(
                depsgraph_update_post)

        unregister_gizmo_system()

        del bpy.types.Armature.hubs_old_bones_length

    return register, unregister


register, unregister = register_functions()
