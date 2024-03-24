const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export fog',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'fog.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const scene = asset.scenes[0];
        assert.strictEqual(utils.checkExtensionAdded(scene, 'MOZ_hubs_components'), true);

        const ext = scene.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "fog": {
                "type": "linear",
                "color": "#0cff00",
                "near": 1,
                "far": 100,
                "density": 0.10000000149011612
            }
        });
    }
};