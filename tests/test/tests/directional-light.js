const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export directional-light',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'directional-light.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "directional-light": {
                "color": "#0cff00",
                "intensity": 1,
                "castShadow": false,
                "shadowMapResolution": [
                    512,
                    512
                ],
                "shadowBias": 0,
                "shadowRadius": 1
            }
        });
    }
};