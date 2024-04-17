const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export spawner',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'spawner.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "spawner": {
                "src": "https://uploads-prod.reticulum.io/files/81e942e8-6ae2-4cc5-b363-f064e9ea3f61.jpg",
                "mediaOptions": {
                    "applyGravity": true
                }
            }
        });
    }
};