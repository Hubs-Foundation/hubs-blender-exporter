const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export environment-settings',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'environment-settings.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const scene = asset.scenes[0];
        assert.strictEqual(utils.checkExtensionAdded(scene, 'MOZ_hubs_components'), true);

        const ext = scene.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "environment-settings": {
                "toneMapping": "LUTToneMapping",
                "toneMappingExposure": 1,
                "backgroundColor": "#0cff00",
                "backgroundTexture": {
                    "__mhc_link_type": "texture",
                    "index": 0
                },
                "envMapTexture": {
                    "__mhc_link_type": "texture",
                    "index": 1
                }
            }
        });
    }
};