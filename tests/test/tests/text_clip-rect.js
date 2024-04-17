const fs = require('fs');
const path = require('path')
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
    description: 'can export text with clip rect property',
    test: outDirPath => {
        let gltfPath = path.resolve(outDirPath, 'text_clip-rect.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
            "text": {
                "value": "Hello World!",
                "fontSize": 0.07500000298023224,
                "textAlign": "left",
                "anchorX": "center",
                "anchorY": "middle",
                "color": "#0cff00",
                "letterSpacing": 0,
                "clipRect": [
                    -0.10000000149011612,
                    -0.20000000298023224,
                    0.30000001192092896,
                    0.4000000059604645
                ],
                "lineHeight": 0,
                "outlineWidth": "0",
                "outlineColor": "#0cff00",
                "outlineBlur": "0",
                "outlineOffsetX": "0",
                "outlineOffsetY": "0",
                "outlineOpacity": 1,
                "fillOpacity": 1,
                "strokeWidth": "0",
                "strokeColor": "#0cff00",
                "strokeOpacity": 1,
                "textIndent": 0,
                "whiteSpace": "normal",
                "overflowWrap": "normal",
                "opacity": 1,
                "side": "front",
                "maxWidth": 1,
                "curveRadius": 0,
                "direction": "auto"
            }
        });
    }
};
