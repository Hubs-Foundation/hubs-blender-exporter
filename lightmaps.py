import bpy

# Find and select the image texture associated with a MOZ_lightmap settings
def findImageTexture(lightmapNode):
    imageTexture = None
    for inputs in lightmapNode.inputs:
        for links in inputs.links:
            return links.from_node
    return None

# Find the UV map associated with an image texture

def findUvMap(imageTexture, material):
    # Search for the parent UV Map
    for inputs in imageTexture.inputs:
        for links in inputs.links:
            # Is this node a MOZ lightmap node?
            if links.from_node.bl_idname == "ShaderNodeUVMap": 
                return links.from_node.uv_map
            else:
                raise ValueError(f"Unexpected node type '{links.from_node.bl_idname}' instead of 'ShaderNodeUVMap' on material '{material.name}'")
    return None

# Select the object that holds this mesh
def selectObjectFromMesh(mesh):
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            if o.data.name == mesh.name:
                # Objects cannot be selected if they are hidden
                o.hide_set(False)
                o.select_set(True)
                print(f" --- selected object '{o.name}' because it uses mesh '{mesh.name}'")                                
                return

# Select the UV input to the image texture for every mesh that uses the given material
def selectUvMaps(imageTexture, material):
    # Select the lightmap UVs on the associated mesh
    uvMap = findUvMap(imageTexture, material)
    if uvMap:                        
        print(f" -- found UV Map Node '{uvMap}'")
        # Search for meshes that use this material (can't find a parent property so this will have to do)
        for mesh in bpy.data.meshes:
            if mesh.materials.find(material.name) != -1:
                print(f" -- found mesh '{mesh.name}' that uses this material")                                
                selectObjectFromMesh(mesh)                          
                if mesh.uv_layers.find(uvMap) != -1:
                    uvLayer = mesh.uv_layers[uvMap]
                    mesh.uv_layers.active = uvLayer
                    print(f" --- UV layer '{uvMap}' is now active on '{mesh.name}'")                                
                else:
                    raise ValueError(f"Failed to find UV layer '{uvMap}' for mesh '{mesh.name}' using material '{material.name}'")
    else:
        raise ValueError(f"No UV map found for image texture '{imageTexture.name}' with image '{imageTexture.image.name}' in material '{material.name}'")

# Selects all MOZ lightmap related components ready for baking
def selectLightmapComponents(targetName):    
    # Deslect all objects to start with (bake objects will be selected)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    # For every material
    for material in bpy.data.materials:
        if material.node_tree:
            # For every node in the material graph
            for shadernode in material.node_tree.nodes:
                # Is this node a MOZ lightmap node?
                if shadernode.bl_idname == "moz_lightmap.node":
                    print(f"found '{shadernode.name}' ({shadernode.label}) on material '{material.name}'")                    
                    imageTexture = findImageTexture(shadernode)                
                    if imageTexture:
                        # Check image texture actually has an image
                        if imageTexture.image == None:
                            raise ValueError(f"No image found on image texture '{imageTexture.name}' ('{imageTexture.label}') in material '{material.name}'")
                        # Is this lightmap texture image being targetted?
                        if targetName == "" or targetName == imageTexture.image.name:
                            # Unselect all nodes so there will be only one remaining selection
                            for n in material.node_tree.nodes:
                                n.select = False
                            # Select and activate the image texture node so it will be targetted by the bake
                            imageTexture.select = True
                            material.node_tree.nodes.active = imageTexture
                            print(f" - selected image texture '{imageTexture.name}' ({imageTexture.label})")

                            selectUvMaps(imageTexture, material)
                        else:
                            print(f"Ignoring image texture '{imageTexture.name}' because it uses image '{imageTexture.image.name}' and the target is '{targetName}'")
                    else:
                        raise ValueError(f"No image texture found on material '{material.name}'")      
                        
# List all the lightmap textures images
def listLightmapImages():
    result = set()
    # For every material
    for material in bpy.data.materials:
        if material.node_tree:
            # For every node in the material graph
            for shadernode in material.node_tree.nodes:
                # Is this node a MOZ lightmap node?
                if shadernode.bl_idname == "moz_lightmap.node":
                    imageTexture = findImageTexture(shadernode)
                    if imageTexture:
                        if imageTexture.image:
                            result.add(imageTexture.image)
    return result
