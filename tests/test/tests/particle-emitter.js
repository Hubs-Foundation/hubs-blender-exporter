const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export particle-emitter',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'particle-emitter.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "particle-emitter": {
                "src": "",
                "startColor": "#0cff00",
                "middleColor": "#0cff00",
                "endColor": "#0cff00",
                "startOpacity": 1,
                "middleOpacity": 1,
                "endOpacity": 1,
                "sizeCurve": "linear",
                "colorCurve": "linear",
                "startSize": 1,
                "endSize": 1,
                "sizeRandomness": 0,
                "ageRandomness": 0,
                "lifetime": 1,
                "lifetimeRandomness": 0,
                "particleCount": 10,
                "startVelocity": {
                    "x": 0,
                    "y": 0,
                    "z": 0
                },
                "endVelocity": {
                    "x": 0,
                    "y": 0,
                    "z": 0
                },
                "velocityCurve": "linear",
                "angularVelocity": 0
            }
        });
    }
};