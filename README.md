# Hubs Exporter for Blender

This addon extends the glTF 2.0 exporter to support the `MOZ_hubs_components` and `MOZ_lightmap` extensions allowing you to add behavior to glTF assets for [Mozilla Hubs](https://hubs.mozilla.com).


# To Install
Find the latest [release](https://github.com/MozillaReality/hubs-blender-exporter/releases) and download the source zip file.   
<img alt="select source file zip" src="https://user-images.githubusercontent.com/4493657/102955067-e8179500-4489-11eb-9f26-c764dfa1e4dc.png" width=400px height=300px />  

In Blender: `Edit > Preferences > Add-ons`  
Click install and select the zip file of the latest release.  
<img width="780" alt="in blender prefs install addon" src="https://user-images.githubusercontent.com/4493657/102955927-dcc56900-448b-11eb-8bfa-07e68b31cffd.png">  

Ensure the hubs component exporter is checked and enabled.  
<img width="494" alt="hubs blender exporter installed" src="https://user-images.githubusercontent.com/4493657/102956859-c9b39880-448d-11eb-9f02-2f529f14c139.png">

# Adding Components

To add components, go to the "Hubs" section of the properties panel for the thing you want to add a component to. Currently adding components is supported on Scenes, Objects, Bones, and Materials.

<img src="https://user-images.githubusercontent.com/130735/84547528-97440a00-acb8-11ea-9f07-24c919796a3c.png" width="300px"/>

Click "Add Component" and select the component you wish to add from the list. Only components appropriate for the object type you are currently editing and have not already been added will be shown.

# Using Lightmaps

To use a lightmap, create a `MOZ_lightmap` node from the `Add > Hubs` menu and hook up a image texture to the `Lightmap` input. Use a `UV Map` node to control what UV set should be used for the lightmap, as you would any other texture in Blender. 

![lightmap node](https://user-images.githubusercontent.com/130735/83931408-65c7bd80-a751-11ea-86b9-a2ae889ec5df.png)

Note that for use in Hubs, you currently **MUST** use the second UV set, as ThreeJS is currently hardcoded to use that for lightmaps. This will likely be fixed in the future so the exporter does not enforce this.

![setting bake UV](https://user-images.githubusercontent.com/130735/83697782-b9e96b00-a5b4-11ea-986b-6690c69d8a3f.png)

# Exporting

This addon works in conjunction with the official glTF exporter, so exporting is done through it. Select "File > Export > glTF 2.0" and then ensure "Hubs Components" is enabled under "Extensions".

![gltf export window](https://user-images.githubusercontent.com/130735/84547591-be9ad700-acb8-11ea-8c58-7b1104f0a3a7.png)

# Import into Hubs

The easiest way to use your scene file is through the Spoke [project creation page](https://hubs.mozilla.com/spoke/projects/create) and selecting _Import From Blender_:

<img width="710" alt="Screenshot 2021-10-31 at 14 05 21" src="https://user-images.githubusercontent.com/303516/139588457-8d9d7835-6101-4cfc-886b-ad3e86c37846.png">

This will bring up the Publish Scene From Blender dialog where you can upload your GLB file and a thumbnail picture for your scene:

<img width="826" alt="Screenshot 2021-10-31 at 14 31 44" src="https://user-images.githubusercontent.com/303516/139588871-ca440552-a270-4feb-9208-65b65ee02b4a.png">

It is also possible to use the GLB file to replace the scene for an existing Hubs room directly by going to Room Settings > Change Scene > Custom Scene and entering the URL of the GLB file. This assumes the file has been already uploaded to an online storage provider.
