const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export skybox',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'skybox.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "skybox": {
                "azimuth": 0.15000000596046448,
                "inclination": 0,
                "luminance": 1,
                "mieCoefficient": 0.004999999888241291,
                "mieDirectionalG": 0.800000011920929,
                "turbidity": 10,
                "rayleigh": 2,
                "distance": 8000
            }
        });
    }
};