import bpy

# Find and select the image texture associated with a MOZ_lightmap settings

def selectImageTexture(lightmapNode, material):
    # Search for the parent image texture
    imageTexture = None
    for inputs in lightmapNode.inputs:
        for links in inputs.links:
            imageTexture = links.from_node
    if imageTexture:
        # Unselect all nodes so there will be only one remaining selection
        for n in material.node_tree.nodes:
            n.select = False
        imageTexture.select = True
        print(f" - selected image texture '{imageTexture.name}' ({imageTexture.label})")
    else:
        print(" ! no image texture found")      
    return imageTexture          

# Find the UV map associated with an image texture

def findUvMap(imageTexture):
    # Search for the parent UV Map
    for inputs in imageTexture.inputs:
        for links in inputs.links:
            # Is this node a MOZ lightmap node?
            if links.from_node.bl_idname == "ShaderNodeUVMap": 
                return links.from_node.uv_map
            else:
                print(f" ! unexpected node type '{links.from_node.bl_idname}' instead of 'ShaderNodeUVMap'")
    return None

# Select the object that holds this mesh

def selectObjectFromMesh(mesh):
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            # if this mesh exists in the dict
            if o.data.name == mesh.name:
                o.select_set(True)
                return

# Select the UV input to the image texture for every mesh that uses the given material

def selectUvMaps(imageTexture, material):
    # Select the lightmap UVs on the associated mesh
    uvMap = findUvMap(imageTexture)
    if uvMap:                        
        print(f" - found UV Map Node '{uvMap}'")
        # Search for meshes that use this material (can't find a parent property so this will have to do)
        for mesh in bpy.data.meshes:
            if mesh.materials.find(material.name) != -1:
                print(f" - found mesh '{mesh.name}' that uses this material")                                
                selectObjectFromMesh(mesh)                          
                if mesh.uv_layers.find(uvMap) != -1:
                    uvLayer = mesh.uv_layers[uvMap]
                    mesh.uv_layers.active = uvLayer
                    print(f" - UV layer '{uvMap}' is now active on '{mesh.name}'")                                
                else:
                    print(f" ! failed to find UV layer '{uvMap}' in '{mesh.name}'")
    else:
        print(f" ! no UV map found")

# Selects all MOZ lightmap related components ready for baking

def selectLightmapComponents():
    # Deslect all objects to start with (only lightmapped objects should be selected)
    bpy.ops.object.select_all(action='DESELECT')
    # For every material
    for material in bpy.data.materials:
        if material.node_tree:
            # For every node in the material graph
            for shadernode in material.node_tree.nodes:
                # Is this node a MOZ lightmap node?
                if shadernode.bl_idname == "moz_lightmap.node":
                    print(f"found '{shadernode.name}' ({shadernode.label}) on material '{material.name}'")
                    # Select just the image texture node and activate it so it will be targetted by the bake
                    imageTexture = selectImageTexture(shadernode, material)
                    material.node_tree.nodes.active = imageTexture
                    if imageTexture:
                        selectUvMaps(imageTexture, material)
                        