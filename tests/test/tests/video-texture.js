const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export video-texture-source and video-texture-target',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'video-texture.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const { node: camera, index: cameraIndex } = utils.nodeWithName(asset, "Camera");
        assert.strictEqual(utils.checkExtensionAdded(camera, 'MOZ_hubs_components'), true);

        const { node: material } = utils.materialWithName(asset, "Material.001");
        assert.strictEqual(utils.checkExtensionAdded(material, 'MOZ_hubs_components'), true);

        const videoTextureSourceExt = camera.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(videoTextureSourceExt, {
            "video-texture-source": {
                "resolution": [
                    1280,
                    720
                ],
                "fps": 15
            }
        });

        const videoTextureTargetExt = material.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(videoTextureTargetExt, {
            "video-texture-target": {
                "targetBaseColorMap": true,
                "targetEmissiveMap": true,
                "srcNode": {
                    "__mhc_link_type": "node",
                    "index": cameraIndex
                }
            }
        });
    }
};