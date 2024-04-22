const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export loop-animation',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'loop-animation.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "loop-animation": {
                "clip": "sample_clip_track_name,sample_clip_action_push_down,sample_clip_action_stash",
                "startOffset": 0,
                "timeScale": 1
            }
        });
    }
};