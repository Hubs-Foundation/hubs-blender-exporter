const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export audio-settings',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'audio-settings.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const scene = asset.scenes[0];
        assert.strictEqual(utils.checkExtensionAdded(scene, 'MOZ_hubs_components'), true);

        const ext = scene.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "audio-settings": {
                "avatarDistanceModel": "inverse",
                "avatarRolloffFactor": 2,
                "avatarRefDistance": 1,
                "avatarMaxDistance": 10000,
                "mediaVolume": 0.5,
                "mediaDistanceModel": "inverse",
                "mediaRolloffFactor": 2,
                "mediaRefDistance": 1,
                "mediaMaxDistance": 10000,
                "mediaConeInnerAngle": 360,
                "mediaConeOuterAngle": 0,
                "mediaConeOuterGain": 0
            }
        });
    }
};