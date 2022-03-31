from ..gizmo_info import GizmoInfo
from ..utils import gizmo_update

MEDIA_FRAME = GizmoInfo(
    id="media-frame",
    name="Media Frame",
    type="GIZMO_GT_cage_3d",
    styles=('BOX'),
    draw_options=[],
    update=gizmo_update
)
