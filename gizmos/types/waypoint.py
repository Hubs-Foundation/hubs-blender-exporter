from ..gizmo_info import GizmoInfo
from .models import spawn_point
from .hubs_gizmo import (HubsGizmo, hubs_gizmo_update)
from os.path import (join, dirname)

WAYPOINT = GizmoInfo(
    name="Waypoint",
    type=HubsGizmo.bl_idname,
    draw_options=[],
    shape=spawn_point.SHAPE,
    path=join(dirname(__file__), "models", "spawn-point.glb"),
    id="__HBA_Gizmo_Waypoint",
    update=hubs_gizmo_update
)
