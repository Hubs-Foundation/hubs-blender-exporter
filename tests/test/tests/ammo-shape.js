const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export ammo-shape',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'ammo-shape.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "ammo-shape": {
                "type": "hull",
                "fit": "all",
                "halfExtents": {
                    "x": 0.5,
                    "y": 0.5,
                    "z": 0.5
                },
                "minHalfExtent": 0,
                "maxHalfExtent": 1000,
                "sphereRadius": 0.5,
                "offset": {
                    "x": 0,
                    "y": 0,
                    "z": 0
                },
                "includeInvisible": false
            }
        });
    }
};