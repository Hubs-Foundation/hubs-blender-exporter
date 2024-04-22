const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export simple-water',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'simple-water.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "simple-water": {
                "color": "#0cff00",
                "opacity": 1,
                "tideHeight": 0.009999999776482582,
                "tideScale": {
                    "x": 1,
                    "y": 1
                },
                "tideSpeed": {
                    "x": 0.5,
                    "y": 0.5
                },
                "waveHeight": 1,
                "waveScale": {
                    "x": 1,
                    "y": 20
                },
                "waveSpeed": {
                    "x": 0.05000000074505806,
                    "y": 6
                },
                "ripplesSpeed": 0.25,
                "ripplesScale": 1
            }
        });
    }
}