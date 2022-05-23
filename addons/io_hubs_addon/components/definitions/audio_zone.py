from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..gizmos import gizmo_update


class AudioZone(HubsComponent):
    _definition = {
        'id': 'audio-zone',
        'name': 'hubs_component_audio_zone',
        'display_name': 'Audio Zone',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'deps': ['networked', 'audio-params'],
        'icon': 'MATCUBE'
    }

    inOut: BoolProperty(name="In Out",
                        description="The zone audio parameters affect the sources inside the zone when the listener is outside",
                        default=True)

    outIn: BoolProperty(name="Out In",
                        description="The zone audio parameters affect the sources outside the zone when the listener is inside",
                        default=True)

    @classmethod
    def create_gizmo(cls, obj, gizmo_group):
        widget = gizmo_group.gizmos.new('GIZMO_GT_cage_3d')
        widget.draw_style = ('BOX')
        widget.matrix_basis = obj.matrix_world.normalized()
        widget.line_width = 3
        widget.color = (0.0, 0.8, 0.0)
        widget.alpha = 0.5
        widget.hide = not obj.visible_get()
        widget.hide_select = True
        widget.scale_basis = 1.0
        widget.use_draw_modal = True
        widget.color_highlight = (0.0, 0.8, 0.0)
        widget.alpha_highlight = 1.0

        op = widget.target_set_operator("transform.translate")
        op.constraint_axis = False, False, False
        op.orient_type = 'LOCAL'
        op.release_confirm = True

        return widget
