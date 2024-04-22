const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export audio-target and zone-audio-source',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'audio-target.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const source = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(source, 'MOZ_hubs_components'), true);

        const target = asset.nodes[1];
        assert.strictEqual(utils.checkExtensionAdded(target, 'MOZ_hubs_components'), true);

        const sourceExt = source.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(sourceExt, {
            "zone-audio-source": {
                "onlyMods": true,
                "muteSelf": true,
                "debug": false
            }
        });

        const targetExt = target.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(targetExt, {
            "audio-target": {
                "srcNode": {
                    "__mhc_link_type": "node",
                    "index": 0
                },
                "minDelay": 0.009999999776482582,
                "maxDelay": 0.029999999329447746,
                "debug": false
            },
            "audio-params": {
                "audioType": "pannernode",
                "gain": 1,
                "distanceModel": "inverse",
                "refDistance": 1,
                "rolloffFactor": 1,
                "maxDistance": 10000,
                "coneInnerAngle": 360,
                "coneOuterAngle": 0,
                "coneOuterGain": 0
            }
        });
    }
};