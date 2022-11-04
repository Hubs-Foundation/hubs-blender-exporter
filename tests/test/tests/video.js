const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export video',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'video.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext["video"], {
            "src": "https://uploads-prod.reticulum.io/files/b4dc97b5-6523-4b61-91ae-d14a80ffd398.mp4",
            "projection": "flat",
            "autoPlay": true,
            "controls": true,
            "loop": true
        });
        assert.deepStrictEqual(ext["audio-params"], {
            "audioType": "pannernode",
            "gain": 1,
            "distanceModel": "inverse",
            "refDistance": 1,
            "rolloffFactor": 1,
            "maxDistance": 10000,
            "coneInnerAngle": 360,
            "coneOuterAngle": 0,
            "coneOuterGain": 0
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
    }
};