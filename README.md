# Hubs Exporter for Blender

This addon extends the glTF 2.0 exporter to support the `MOZ_hubs_components` and `MOZ_lightmap` extensions allowing you to add behavior to glTF assets for [Mozilla Hubs](https://hubs.mozilla.com).

# To Install

Find the latest [release](https://github.com/MozillaReality/hubs-blender-exporter/releases) and download the add-on zip file.

<img alt="select add-on zip file" src="https://user-images.githubusercontent.com/837184/204576860-316b32de-8654-48a7-b9a7-3c0de1c1b652.png" width=685px height=330px />

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

# Development

## Code Completion
To enable code completion for the Blender Python API you can install the [Fake Blender Python API module collection](https://github.com/nutti/fake-bpy-module/). You can download the modules using the `setup.sh` script from the repository root or using [pip](https://github.com/nutti/fake-bpy-module/#install-via-pip-package).
## Code style

Tis repository follows the [PEP8](https://peps.python.org/pep-0008/) style convention for python files. If you use VSCode this repository already includes a setting to autoformat every python file when saved. If you don't use VSCode you can probably add a similar setting in your favorite editor. We are happy to add settings for other editors so feel free to open a PR if you want you editor's settings included.

We also includes a `format.py` python script that will formats the whole codebase when run. You can run it before pushing the PR to make sure that all the new code follows PEP8.

Both the python script and the VSCode settings rely on the [autopep8](https://pypi.org/project/autopep8/) command line tool for formatting so make sure that it's installed in your system.

## Addon development

It might be useful while developing to be able to load the addon directly from the checkout folder without needing to install it. You can do it in two ways:

- ### Overriding the Blender user scripts directory
  You can override the Blender user scripts directory from the console to point to the addon repo directory.

**MacOS**

`BLENDER_USER_SCRIPTS=full_path_to_/hubs-blender-exporter /Applications/Blender.app/Contents/MacOS/Blender`

**Linux**

`BLENDER_USER_SCRIPTS=full_path_to_/hubs-blender-exporter blender`

- ### Symlinking your addon to the Blender user scripts directory
  You can create a symbolic link pointing to `full_path_to_/hubs-blender-exporter/addons/io_hubs_addon` in your current Python scripts directory in Blender. This way you will also load any other addons that you have in that directory.

**MacOS and Linux**

`ln -s full_path_to/hubs-blender-exporter/addons/io_hubs_addon full_path_to/blender_user_scrips_dir`

You can set or see the current Blender user scripts in the Preferences -> File Paths -> Scripts

# Debugging

You can debug the addon code with PyCharm or VSCode:

- [Debug with PyCharm](https://code.blender.org/2015/10/debugging-python-code-with-pycharm) **NOTE:** If you are using Blender 2.80+, you need the [updated debugger script](https://github.com/ux3d/random-blender-addons/blob/master/remote_debugger.py)
- [Debug with VSCode](DEBUGGING.md)

# Continuous Integration Tests

To run the tests locally, your system should have a blender executable in the path that launches the desired version of Blender.

The latest version of [Yarn](https://yarnpkg.com/en/) should also be installed.

Then, in the tests folder of this repository, run yarn install, followed by yarn run test.
