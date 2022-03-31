from ..gizmo_info import GizmoInfo
from .models import spawn_point
from ..gizmo_custom import HubsGizmo
from ..utils import hubs_gizmo_update
from os.path import (join, dirname)


WAYPOINT = GizmoInfo(
    id="waypoint",
    name="Waypoint",
    type=HubsGizmo.bl_idname,
    draw_options=[],
    shape=spawn_point.SHAPE,
    path=join(dirname(__file__), "models", "spawn-point.glb"), # Used in case of loading from GLB (disabled at the moment)
    update=hubs_gizmo_update
)
