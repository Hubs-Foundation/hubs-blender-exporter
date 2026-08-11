const fs = require('fs');
const path = require('path');
const assert = require('assert');
const utils = require('../utils.js');

module.exports = {
  description: 'can export rigid-body',
  test: outDirPath => {
    let gltfPath = path.resolve(outDirPath, 'rigid-body.gltf');
    const asset = JSON.parse(fs.readFileSync(gltfPath));

    assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
    assert.strictEqual(utils.checkExtensionAdded(asset, 'MOZ_hubs_components'), true);

    const node = asset.nodes[0];
    assert.strictEqual(utils.checkExtensionAdded(node, 'MOZ_hubs_components'), true);

    const ext = node.extensions['MOZ_hubs_components'];
    assert.deepStrictEqual(ext, {
      "rigidbody":{
        "type":"dynamic",
        "disableCollision":false,
        "collisionGroup":"objects",
        "collisionMask":[
          "objects",
          "triggers",
          "environment"
        ],
        "mass":1,
        "linearDamping":0,
        "angularDamping":0,
        "linearSleepingThreshold":0.800000011920929,
        "angularSleepingThreshold":1,
        "angularFactor":[
          1,
          1,
          1
        ],
        "gravity":[
          0,
          -9.800000190734863,
          0
        ]
      },
      "physics-shape":{
        "type":"hull",
        "fit":"all",
        "halfExtents":{
          "x":0.5,
          "y":0.5,
          "z":0.5
        },
        "minHalfExtent":0,
        "maxHalfExtent":1000,
        "sphereRadius":0.5,
        "offset":{
          "x":0,
          "y":0,
          "z":0
        },
        "includeInvisible":false
      }
    });
  }
};