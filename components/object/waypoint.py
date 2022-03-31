import bpy
from bpy.props import BoolProperty, PointerProperty
from bpy.types import PropertyGroup
from ..utils import *

COMPONENT_NAME = "waypoint"


class WaypointComponentProperties(PropertyGroup):
    canBeSpawnPoint: BoolProperty(
        name="canBeSpawnPoint",
        description="After each use, this waypoint will be disabled until the previous user moves away from it",
        default=False)
    canBeOccupied: BoolProperty(
        name="canBeOccupied",
        description="After each use, this waypoint will be disabled until the previous user moves away from it",
        default=False)
    canBeClicked: BoolProperty(
        name="canBeClicked",
        description="This waypoint will be visible in pause mode and clicking on it will teleport you to it",
        default=False)
    willDisableMotion: BoolProperty(
        name="willDisableMotion",
        description="Avatars will not be able to move while occupying his waypoint",
        default=False)
    willDisableTeleporting: BoolProperty(
        name="willDisableTeleporting",
        description="Avatars will not be able to teleport while occupying this waypoint",
        default=False)
    willMaintainInitialOrientation: BoolProperty(
        name="willMaintainInitialOrientation",
        description="Instead of rotating to face the same direction as the waypoint, avatars will maintain the orientation they started with before they teleported",
        default=False)
    snapToNavMesh: BoolProperty(
        name="snapToNavMesh",
        description="Avatars will move as close as they can to this waypoint but will not leave the ground",
        default=False)


class HBAComponentWaypointAdd(bpy.types.Operator):
    bl_idname = "object.hba_component_waypoint_add"
    bl_label = "Add Waypoint Component"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        add_component(context.object, COMPONENT_NAME)
        add_gizmo(context.object, COMPONENT_NAME)

        return {"FINISHED"}


class HBAComponentWaypointPanel(bpy.types.Panel):
    bl_idname = "HBA_PT_Component_Waypoint"
    bl_label = "Waypoint Component"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Hubs'

    @classmethod
    def poll(cls, context):
        return has_component(context.object, COMPONENT_NAME)

    def draw(self, context):
        obj = context.object

        layout = self.layout
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "canBeSpawnPoint",
                 text="Use as Spawn Point")
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "canBeOccupied",
                 text="Can be occupied")
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "canBeClicked",
                 text="Clickable")
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "willDisableMotion",
                 text="Disable motion")
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "willDisableTeleporting",
                 text="Disable teleporting")
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "willMaintainInitialOrientation",
                 text="Maintain initial orientation")
        row = layout.row()
        row.prop(obj.hubs_component_waypoint,
                 "snapToNavMesh",
                 text="Snap to navmesh")
        row = layout.row()


def register():
    bpy.utils.register_class(WaypointComponentProperties)
    bpy.types.Object.hubs_component_waypoint = PointerProperty(
        type=WaypointComponentProperties)
    bpy.utils.register_class(HBAComponentWaypointAdd)
    bpy.utils.register_class(HBAComponentWaypointPanel)


def unregister():
    bpy.utils.unregister_class(HBAComponentWaypointPanel)
    bpy.utils.unregister_class(HBAComponentWaypointAdd)
    del bpy.types.Object.hubs_component_waypoint
    bpy.utils.unregister_class(WaypointComponentProperties)
