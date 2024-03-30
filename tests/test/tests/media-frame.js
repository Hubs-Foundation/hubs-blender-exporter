const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export media-frame',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'media-frame.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext['media-frame'], {
            align: {
                "x": 'center',
                "y": 'center',
                "z": 'center'
            },
            "bounds": {
                "x": 1,
                "y": 1,
                "z": 4
            },
            "mediaType": "all-2d",
            "snapToCenter": true,
            "scaleToBounds": true
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
    }
};
