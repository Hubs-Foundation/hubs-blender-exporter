import bpy

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from bpy.types import Node


class MozCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'


node_categories = [
    MozCategory("MOZ_NODES", "Hubs", items=[
        NodeItem("moz_lightmap.node")
    ]),
]


class MozLightmapNode(Node):
    """MOZ_lightmap settings node"""
    bl_idname = 'moz_lightmap.node'
    bl_label = 'MOZ_lightmap settings'
    bl_icon = 'LIGHT'
    bl_width_min = 216.3
    bl_width_max = 330.0

    intensity: bpy.props.FloatProperty(
        name="Intensity", soft_min=0, soft_max=1, default=1)

    def init(self, context):
        lightmap = self.inputs.new('NodeSocketColor', "Lightmap")
        lightmap.hide_value = True

        self.width = 216.3

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ShaderNodeTree'

    def draw_buttons(self, context, layout):
        layout.prop(self, "intensity")

    def draw_label(self):
        return "MOZ_lightmap"


def register():
    bpy.utils.register_class(MozLightmapNode)
    nodeitems_utils.register_node_categories("MOZ_NODES", node_categories)


def unregister():
    bpy.utils.unregister_class(MozLightmapNode)
    nodeitems_utils.unregister_node_categories("MOZ_NODES")
