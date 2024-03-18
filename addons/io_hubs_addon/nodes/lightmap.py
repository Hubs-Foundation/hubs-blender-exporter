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

class NODE_MT_mozilla_hubs_nodes(bpy.types.Menu):
    bl_label = "Hubs"
    bl_idname = "NODE_MT_mozilla_hubs_nodes"

    def draw(self, context):
        layout = self.layout
        # Example of adding a custom node to the menu
        layout.operator("node.add_node", text="MOZ_lightmap settings").type = "moz_lightmap.node"

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

def create_node_categories():
    return [NodeCategory("MOZ_NODES", "Moz Nodes", items=node_categories)]

def menu_func(self, context):
    self.layout.menu("NODE_MT_mozilla_hubs_nodes")

def register_blender_4():
    print("Using Blender 4x")
    bpy.utils.register_class(NODE_MT_mozilla_hubs_nodes)
    bpy.types.NODE_MT_shader_node_add_all.append(menu_func)
    bpy.utils.register_class(MozLightmapNode)

def unregister_blender_4():
    bpy.types.NODE_MT_shader_node_add_all.remove(menu_func)
    bpy.utils.unregister_class(NODE_MT_mozilla_hubs_nodes)
    bpy.utils.unregister_class(MozLightmapNode)

def register_blender_3():
    print("Using Blender 3x")

    bpy.utils.register_class(MozLightmapNode)
    nodeitems_utils.register_manual_map(create_node_categories)

def unregister_blender_3():
    bpy.utils.unregister_class(MozLightmapNode)
    nodeitems_utils.unregister_manual_map(create_node_categories)

def register():
    if bpy.app.version < (4, 0, 0):
        register_blender_3()
    else:
        register_blender_4()

def unregister():
    if bpy.app.version < (4, 0, 0):
        unregister_blender_3()
    else:
        unregister_blender_4()