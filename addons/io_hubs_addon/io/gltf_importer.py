import bpy
from bpy.props import BoolProperty, PointerProperty


if bpy.app.version >= (4, 3, 0):
    from io_scene_gltf2.blender.imp.node import BlenderNode
    from io_scene_gltf2.blender.imp.material import BlenderMaterial
    from io_scene_gltf2.blender.imp.scene import BlenderScene
    from io_scene_gltf2.blender.imp.image import BlenderImage

else:
    from io_scene_gltf2.blender.imp.gltf2_blender_node import BlenderNode
    from io_scene_gltf2.blender.imp.gltf2_blender_material import BlenderMaterial
    from io_scene_gltf2.blender.imp.gltf2_blender_scene import BlenderScene
    from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage
    
from .utils import HUBS_CONFIG, import_image, import_all_textures
from ..components.components_registry import get_component_by_name
import traceback

EXTENSION_NAME = HUBS_CONFIG["gltfExtensionName"]

armatures = {}
delayed_gathers = []
import_report = []


def call_delayed_gathers():
    global delayed_gathers
    global import_report
    for gather_import in delayed_gathers:
        gather_import_args = gather_import.__closure__[0].cell_contents
        blender_host = gather_import_args[2]
        component_name = gather_import_args[3]
        try:
            gather_import()
        except Exception:
            traceback.print_exc()
            print(f"Failed to import {component_name} component on {blender_host.name} continuing on...")
            import_report.append(
                f"Failed to import {component_name} component on {blender_host.name}.  See the console for details.")
    delayed_gathers.clear()


def import_hubs_components(gltf_node, blender_host, gltf, blender_ob=None):
    global import_report
    if gltf_node and gltf_node.extensions and EXTENSION_NAME in gltf_node.extensions:
        components_data = gltf_node.extensions[EXTENSION_NAME]
        for component_name in components_data.keys():
            component_class = get_component_by_name(component_name)
            if component_class:
                component_value = components_data[component_name]
                try:
                    data = component_class.gather_import(
                        gltf, blender_host, component_name, component_value, import_report, blender_ob=blender_ob)
                    if data and hasattr(data, "delayed_gather"):
                        global delayed_gathers
                        delayed_gathers.append((data))
                except Exception:
                    traceback.print_exc()
                    print(f"Failed to import {component_name} component on {blender_host.name} continuing on...")
                    import_report.append(
                        f"Failed to import {component_name} component on {blender_host.name}.  See the console for details.")
            else:
                if component_name != "heightfield":
                    # heightfield is a Spoke-only component and not needed in Blender.
                    print(f'Could not import unsupported component "{component_name}"')
                    import_report.append(
                        f"Could not import unsupported component {component_name} component on {blender_host.name}.")


def add_lightmap(gltf_material, blender_mat, gltf):
    if gltf_material and gltf_material.extensions and 'MOZ_lightmap' in gltf_material.extensions:
        extension = gltf_material.extensions['MOZ_lightmap']

        texture_index = extension['index']

        gltf_texture = gltf.data.textures[texture_index]
        blender_image_name, _ = import_image(gltf, gltf_texture)
        blender_image = bpy.data.images[blender_image_name]

        blender_mat.use_nodes = True
        nodes = blender_mat.node_tree.nodes
        lightmap_node = nodes.new('moz_lightmap.node')
        lightmap_node.location = (-300, 0)
        lightmap_node.intensity = extension['intensity']
        node_tex = nodes.new('ShaderNodeTexImage')
        node_tex.image = blender_image
        node_tex.location = (-600, 0)
        blender_mat.node_tree.links.new(
            node_tex.outputs["Color"], lightmap_node.inputs["Lightmap"])
        node_uv = nodes.new('ShaderNodeUVMap')
        node_uv.uv_map = 'UVMap.%03d' % 1
        node_uv.location = (-900, 0)
        blender_mat.node_tree.links.new(
            node_uv.outputs["UV"], node_tex.inputs["Vector"])


def add_bones(gltf):
    # Bones are created after the armatures so we need to wait until all nodes have been processed to be able to access the bones objects
    global armatures
    for armature in armatures.values():
        blender_object = armature['armature']
        gltf_bones = armature['gltf_bones']
        for bone in blender_object.data.bones:
            gltf_bone = gltf_bones[bone.name]
            import_hubs_components(
                gltf_bone, bone, gltf, blender_ob=blender_object)


def store_bones_for_import(gltf, vnode):
    # Store the glTF bones with the armature so their components can be imported once the Blender bones are created.
    global armatures
    children = vnode.children[:]
    gltf_bones = {}
    while children:
        child_index = children.pop()
        child_vnode = gltf.vnodes[child_index]
        if child_vnode.type == vnode.Bone:
            gltf_bones[child_vnode.name] = gltf.data.nodes[child_index]
            children.extend(child_vnode.children)

    armatures[vnode.blender_object.name] = {
        'armature': vnode.blender_object, 'gltf_bones': gltf_bones}


def show_import_report():
    global import_report
    if not import_report:
        return

    title = "Import Report"

    def report_import():
        bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title=title, report_string='\n\n'.join(import_report))
    bpy.app.timers.register(report_import)


class glTF2ImportUserExtension:

    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.extensions = [
            Extension(name=EXTENSION_NAME, extension={}, required=True)]
        self.properties = bpy.context.scene.HubsComponentsExtensionImportProperties
        global delayed_gathers
        delayed_gathers.clear()

    def gather_import_scene_before_hook(self, gltf_scene, blender_scene, gltf):
        if not self.properties.enabled:
            return

        global armatures
        armatures.clear()
        global delayed_gathers
        delayed_gathers.clear()
        global import_report
        import_report.clear()

        if gltf.data.asset and gltf.data.asset.extras:
            if 'gltf_yup' in gltf.data.asset.extras:
                gltf.import_settings['gltf_yup'] = gltf.data.asset.extras[
                    'gltf_yup']

        import_all_textures(gltf)

    def gather_import_scene_after_nodes_hook(self, gltf_scene, blender_scene, gltf):
        if not self.properties.enabled:
            return

        import_hubs_components(gltf_scene, blender_scene, gltf)

        add_bones(gltf)
        armatures.clear()

    def gather_import_node_after_hook(self, vnode, gltf_node, blender_object, gltf):
        if not self.properties.enabled:
            return

        import_hubs_components(
            gltf_node, blender_object, gltf, blender_ob=blender_object)

        #  Node hooks are not called for bones. Bones are created together with their armature.
        # Unfortunately the bones are created after this hook is called so we need to wait until all nodes have been created.
        if vnode.is_arma:
            store_bones_for_import(gltf, vnode)

    def gather_import_image_after_hook(self, gltf_img, blender_image, gltf):
        # As of Blender 3.2.0 the importer doesn't import images that are not referenced by a material socket.
        # We handle this case by case in each component's gather_import override.
        pass

    def gather_import_texture_after_hook(
            self, gltf_texture, node_tree, mh, tex_info, location, label, color_socket, alpha_socket, is_data, gltf):
        # As of Blender 3.2.0 the importer doesn't import textures that are not referenced by a material socket image.
        # We handle this case by case in each component's gather_import override.
        pass

    def gather_import_material_after_hook(self, gltf_material, vertex_color, blender_mat, gltf):
        if not self.properties.enabled:
            return

        import_hubs_components(
            gltf_material, blender_mat, gltf)

        add_lightmap(gltf_material, blender_mat, gltf)

    def gather_import_scene_after_animation_hook(self, gltf_scene, blender_scene, gltf):
        call_delayed_gathers()
        show_import_report()


# import hooks were only recently added to the glTF exporter, so make a custom hook for now
orig_BlenderNode_create_object = BlenderNode.create_object
orig_BlenderMaterial_create = BlenderMaterial.create
orig_BlenderScene_create = BlenderScene.create


@ staticmethod
def patched_BlenderNode_create_object(gltf, vnode_id):
    blender_object = orig_BlenderNode_create_object(gltf, vnode_id)

    vnode = gltf.vnodes[vnode_id]
    node = None

    if vnode.camera_node_idx is not None:
        parent_vnode = gltf.vnodes[vnode.parent]
        node = gltf.data.nodes[vnode.parent]
        if node.name != parent_vnode.name:
            if parent_vnode.name:
                print("Falling back to getting the node from the vnode name.")
                node = [n for n in gltf.data.nodes if n.name == parent_vnode.name][0]
            else:
                print("Couldn't find the equivalent node for the vnode.")

    else:
        node = gltf.data.nodes[vnode_id]
        if node.name != vnode.name:
            if vnode.name:
                print("Falling back to getting the node from the vnode name.")
                node = [n for n in gltf.data.nodes if n.name == vnode.name][0]
            else:
                print("Couldn't find the equivalent node for the vnode.")

    import_hubs_components(node, vnode.blender_object, gltf, blender_ob=vnode.blender_object)

    #  Node hooks are not called for bones. Bones are created together with their armature.
    # Unfortunately the bones are created after this hook is called so we need to wait until all nodes have been created.
    if vnode.is_arma:
        store_bones_for_import(gltf, vnode)

    return blender_object


@ staticmethod
def patched_BlenderMaterial_create(gltf, material_idx, vertex_color):
    orig_BlenderMaterial_create(
        gltf, material_idx, vertex_color)
    gltf_material = gltf.data.materials[material_idx]
    blender_mat_name = next(iter(gltf_material.blender_material.values()))
    blender_mat = bpy.data.materials[blender_mat_name]
    import_hubs_components(gltf_material, blender_mat, gltf)

    add_lightmap(gltf_material, blender_mat, gltf)


@ staticmethod
def patched_BlenderScene_create(gltf):
    global armatures
    global delayed_gathers
    global import_report
    armatures.clear()
    delayed_gathers.clear()
    import_report.clear()

    import_all_textures(gltf)
    orig_BlenderScene_create(gltf)
    gltf_scene = gltf.data.scenes[gltf.data.scene]
    blender_object = bpy.data.scenes[gltf.blender_scene]
    import_hubs_components(gltf_scene, blender_object, gltf)

    # Bones are created after the armatures so we need to wait until all nodes have been processed to be able to access the bones objects
    add_bones(gltf)
    armatures.clear()

    call_delayed_gathers()
    show_import_report()


class HubsGLTFImportPanel(bpy.types.Panel):

    bl_idname = "HBA_PT_Import_Panel"
    bl_label = "Hubs Import Panel"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Hubs Components"
    bl_parent_id = "GLTF_PT_import_user_extensions"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "IMPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        props = bpy.context.scene.HubsComponentsExtensionImportProperties
        self.layout.prop(props, 'enabled', text="")

    def draw(self, context):
        self.draw_body(context, self.layout)

    @staticmethod
    def draw_body(context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = bpy.context.scene.HubsComponentsExtensionImportProperties
        layout.active = props.enabled

        box = layout.box()
        box.label(text="No options yet")


class HubsImportProperties(bpy.types.PropertyGroup):
    enabled: BoolProperty(
        name="Import Hubs Components",
        description='Import Hubs components from the glTF file',
        default=True
    )


def register():
    print("Register glTF Importer")
    if bpy.app.version < (3, 1, 0):
        BlenderNode.create_object = patched_BlenderNode_create_object
        BlenderMaterial.create = patched_BlenderMaterial_create
        BlenderScene.create = patched_BlenderScene_create
    bpy.utils.register_class(HubsImportProperties)
    bpy.types.Scene.HubsComponentsExtensionImportProperties = PointerProperty(
        type=HubsImportProperties)


def unregister():
    print("Unregister glTF Importer")
    if bpy.app.version < (3, 1, 0):
        BlenderNode.create_object = orig_BlenderNode_create_object
        BlenderMaterial.create = orig_BlenderMaterial_create
        BlenderScene.create = orig_BlenderScene_create
    del bpy.types.Scene.HubsComponentsExtensionImportProperties
    bpy.utils.unregister_class(HubsImportProperties)
