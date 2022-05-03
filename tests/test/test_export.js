const fs = require('fs');
const path = require('path');

const OUT_PREFIX = process.env.OUT_PREFIX || '../tests_out';

process.env['BLENDER_USER_SCRIPTS'] = path.join(process.cwd(), '..');

const blenderVersions = (() => {
  if (process.platform == 'darwin') {
    return [
      "/Applications/Blender.app/Contents/MacOS/Blender"
    ];
  }
  else if (process.platform == 'linux') {
    return [
      "blender"
    ];
  }
})();

var utils = require('./utils.js').utils;

var assert = require('assert');

describe('Exporter', function () {
  let blenderSampleScenes = fs.readdirSync('scenes').filter(f => f.endsWith('.blend')).map(f => f.substring(0, f.length - 6));

  blenderVersions.forEach(function (blenderVersion) {
    let variants = [
      ['', ''],
      ['_glb', '--glb']
    ];

    variants.forEach(function (variant) {
      const args = variant[1];
      describe(blenderVersion + '_export' + variant[0], function () {
        blenderSampleScenes.forEach((scene) => {
          it(scene, function (done) {
            let outDirName = 'out' + blenderVersion + variant[0];
            let blenderPath = `scenes/${scene}.blend`;
            let ext = args.indexOf('--glb') === -1 ? '.gltf' : '.glb';
            let outDirPath = path.resolve(OUT_PREFIX, 'scenes', outDirName);
            let dstPath = path.resolve(outDirPath, `${scene}${ext}`);
            utils.blenderFileToGltf(blenderVersion, blenderPath, outDirPath, (error) => {
              if (error)
                return done(error);

              utils.validateGltf(dstPath, done);
            }, args);
          });
        });
      });
    });

    describe(blenderVersion + '_export_results', function () {
      let outDirName = 'out' + blenderVersion;
      let outDirPath = path.resolve(OUT_PREFIX, 'scenes', outDirName);

      it('can export link', function () {
        let gltfPath = path.resolve(outDirPath, 'link.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext['link'], { href: 'https://hubs.mozilla.com' });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
      });

      it('can export visible', function () {
        let gltfPath = path.resolve(outDirPath, 'visible.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, { visible: { visible: true } });
      });

      it('can export nav-mesh', function () {
        let gltfPath = path.resolve(outDirPath, 'nav-mesh.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, { 'nav-mesh': {} });
      });

      it('can export video-texture-source and video-texture-target', function () {
        let gltfPath = path.resolve(outDirPath, 'video-texture.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const camera = asset.nodes[1];
        assert.strictEqual(utils.checkExtensionAdded(camera), true);

        const material = asset.materials[0];
        assert.strictEqual(utils.checkExtensionAdded(material), true);

        const videoTextureSourceExt = camera.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(videoTextureSourceExt, {
          "video-texture-source": {
            "resolution": [
              1280,
              720
            ],
            "fps": 15
          }
        });

        const videoTextureTargetExt = material.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(videoTextureTargetExt, {
          "video-texture-target": {
            "targetBaseColorMap": true,
            "targetEmissiveMap": true,
            "srcNode": {
              "__mhc_link_type": "node",
              "index": 1
            }
          }
        });
      });

      it('can export ammo-shape', function () {
        let gltfPath = path.resolve(outDirPath, 'ammo-shape.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "ammo-shape": {
            "type": "hull",
            "fit": "all",
            "halfExtents": {
              "x": 0.5,
              "y": 0.5,
              "z": 0.5
            },
            "minHalfExtent": 0,
            "maxHalfExtent": 1000,
            "sphereRadius": 0.5,
            "offset": {
              "x": 0,
              "y": 0,
              "z": 0
            },
            "includeInvisible": false
          }
        });
      });

      it('can export skybox', function () {
        let gltfPath = path.resolve(outDirPath, 'skybox.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

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
      });

      it('can export reflection-probe', function () {
        let gltfPath = path.resolve(outDirPath, 'reflection-probe.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[3];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "reflection-probe": {
            "size": 2.5,
            "envMapTexture": {
              "__mhc_link_type": "texture",
              "index": 0
            }
          }
        });
      });

      it('can export directional-light', function () {
        let gltfPath = path.resolve(outDirPath, 'directional-light.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "directional-light": {
            "color": "#ffffff",
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
      });

      it('can export point-light', function () {
        let gltfPath = path.resolve(outDirPath, 'point-light.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "point-light": {
            "color": "#ffffff",
            "intensity": 1,
            "range": 0,
            "decay": 2,
            "castShadow": false,
            "shadowMapResolution": [
              512,
              512
            ],
            "shadowBias": 0,
            "shadowRadius": 1
          }
        });
      });

      it('can export spot-light', function () {
        let gltfPath = path.resolve(outDirPath, 'spot-light.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "spot-light": {
            "color": "#ffffff",
            "intensity": 1,
            "range": 0,
            "decay": 2,
            "innerConeAngle": 0,
            "outerConeAngle": 0.7853981852531433,
            "castShadow": false,
            "shadowMapResolution": [
              512,
              512
            ],
            "shadowBias": 0,
            "shadowRadius": 1
          }
        });
      });

      it('can export ambient-light', function () {
        let gltfPath = path.resolve(outDirPath, 'ambient-light.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "ambient-light": {
            "color": "#ffffff",
            "intensity": 1
          }
        });
      });

      it('can export particle-emitter', function () {
        let gltfPath = path.resolve(outDirPath, 'particle-emitter.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "particle-emitter": {
            "src": "",
            "startColor": "#ffffff",
            "middleColor": "#ffffff",
            "endColor": "#ffffff",
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
      });

      it('can export particle-emitter', function () {
        let gltfPath = path.resolve(outDirPath, 'particle-emitter.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "particle-emitter": {
            "src": "",
            "startColor": "#ffffff",
            "middleColor": "#ffffff",
            "endColor": "#ffffff",
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
      });

      it('can export waypoint', function () {
        let gltfPath = path.resolve(outDirPath, 'waypoint.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "waypoint": {
            "canBeSpawnPoint": false,
            "canBeOccupied": false,
            "canBeClicked": false,
            "willDisableMotion": false,
            "willDisableTeleporting": false,
            "snapToNavMesh": false,
            "willMaintainInitialOrientation": false,
            "willMaintainWorldUp": true,
            "isOccupied": false
          }
        });
      });

      it('can export image', function () {
        let gltfPath = path.resolve(outDirPath, 'image.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext["image"], {
          "src": "https://uploads-prod.reticulum.io/files/81e942e8-6ae2-4cc5-b363-f064e9ea3f61.jpg",
          "controls": true,
          "alphaMode": "opaque",
          "projection": "flat"
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
      });

      it('can export audio', function () {
        let gltfPath = path.resolve(outDirPath, 'audio.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext["audio"], {
          "src": "https://uploads-prod.reticulum.io/files/a3670163-1e78-485c-b70d-9af51f6afaff.mp3",
          "autoPlay": true,
          "controls": true,
          "loop": true
        });
        assert.deepStrictEqual(ext["audio-params"], {
          "audioType": "pannernode",
          "gain": 1,
          "distanceModel": "inverse",
          "refDistance": 1,
          "rolloffFactor": 1,
          "maxDistance": 10000,
          "coneInnerAngle": 360,
          "coneOuterAngle": 0,
          "coneOuterGain": 0
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
      });

      it('can export video', function () {
        let gltfPath = path.resolve(outDirPath, 'video.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext["video"], {
          "src": "https://uploads-prod.reticulum.io/files/b4dc97b5-6523-4b61-91ae-d14a80ffd398.mp4",
          "projection": "flat",
          "autoPlay": true,
          "controls": true,
          "loop": true
        });
        assert.deepStrictEqual(ext["audio-params"], {
          "audioType": "pannernode",
          "gain": 1,
          "distanceModel": "inverse",
          "refDistance": 1,
          "rolloffFactor": 1,
          "maxDistance": 10000,
          "coneInnerAngle": 360,
          "coneOuterAngle": 0,
          "coneOuterGain": 0
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
      });

      it('can export billboard', function () {
        let gltfPath = path.resolve(outDirPath, 'billboard.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "billboard": {
            "onlyY": false
          }
        });
      });

      it('can export text', function () {
        let gltfPath = path.resolve(outDirPath, 'text.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "text": {
            "value": "Hello World",
            "align": "left",
            "baseline": "top",
            "side": "front",
            "whiteSpace": "normal",
            "font": "roboto",
            "color": "#ffffff",
            "width": 1,
            "wrapCount": 40,
            "wrapPixels": 0,
            "letterSpacing": 0,
            "lineHeight": 0,
            "opacity": 1,
            "xOffset": 0,
            "zOffset": 0.0010000000474974513
          }
        });
      });

      it('can export media-frame', function () {
        let gltfPath = path.resolve(outDirPath, 'media-frame.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext['media-frame'], {
          "bounds": {
            "x": 1,
            "y": 1,
            "z": 1
          },
          "mediaType": "all-2d",
          "snapToCenter": true
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
      });

      it('can export spawner', function () {
        let gltfPath = path.resolve(outDirPath, 'spawner.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "spawner": {
            "src": "https://uploads-prod.reticulum.io/files/81e942e8-6ae2-4cc5-b363-f064e9ea3f61.jpg",
            "mediaOptions": {
              "applyGravity": false
            }
          }
        });
      });

      it('can export audio-target and zone-audio-source', function () {
        let gltfPath = path.resolve(outDirPath, 'audio-target.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const source = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(source), true);

        const target = asset.nodes[1];
        assert.strictEqual(utils.checkExtensionAdded(target), true);

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
      });

      it('can export audio-zone', function () {
        let gltfPath = path.resolve(outDirPath, 'audio-zone.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext["audio-zone"], {
          "inOut": true,
          "outIn": true
        });
        assert.deepStrictEqual(ext["audio-params"], {
          "audioType": "pannernode",
          "gain": 1,
          "distanceModel": "inverse",
          "refDistance": 1,
          "rolloffFactor": 1,
          "maxDistance": 10000,
          "coneInnerAngle": 360,
          "coneOuterAngle": 0,
          "coneOuterGain": 0
        });
        assert.strictEqual(utils.UUID_REGEX.test(ext['networked']['id']), true);
      });

      it('can export shadow', function () {
        let gltfPath = path.resolve(outDirPath, 'shadow.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "shadow": {
            "cast": true,
            "receive": true
          }
        });
      });

      it('can export uv-scroll', function () {
        let gltfPath = path.resolve(outDirPath, 'uv-scroll.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "uv-scroll": {
            "speed": {
              "x": 0,
              "y": 0
            },
            "increment": {
              "x": 0,
              "y": 0
            }
          }
        });
      });

      it('can export loop-animation', function () {
        let gltfPath = path.resolve(outDirPath, 'loop-animation.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "loop-animation": {
            "clip": "sample_clip",
            "paused": false
          }
        });
      });

      it('can export personal-space-invader', function () {
        let gltfPath = path.resolve(outDirPath, 'personal-space-invader.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "personal-space-invader": {
            "radius": 0.10000000149011612,
            "useMaterial": false,
            "invadingOpacity": 0.30000001192092896
          }
        });
      });

      it('can export scale-audio-feedback', function () {
        let gltfPath = path.resolve(outDirPath, 'scale-audio-feedback.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "scale-audio-feedback": {
            "minScale": 1,
            "maxScale": 1.5
          }
        });
      });

      it('can export morph-audio-feedback', function () {
        let gltfPath = path.resolve(outDirPath, 'morph-audio-feedback.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const node = asset.nodes[0];
        assert.strictEqual(utils.checkExtensionAdded(node), true);

        const ext = node.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "morph-audio-feedback": {
            "name": "Key 1",
            "minValue": 0,
            "maxValue": 1
          }
        });
      });

      it('can export fog', function () {
        let gltfPath = path.resolve(outDirPath, 'fog.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const scene = asset.scenes[0];
        assert.strictEqual(utils.checkExtensionAdded(scene), true);

        const ext = scene.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "fog": {
            "type": "linear",
            "color": "#ffffff",
            "near": 1,
            "far": 100,
            "density": 0.10000000149011612
          }
        });
      });

      it('can export audio-settings', function () {
        let gltfPath = path.resolve(outDirPath, 'audio-settings.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const scene = asset.scenes[0];
        assert.strictEqual(utils.checkExtensionAdded(scene), true);

        const ext = scene.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "audio-settings": {
            "avatarDistanceModel": "inverse",
            "avatarRolloffFactor": 2,
            "avatarRefDistance": 1,
            "avatarMaxDistance": 10000,
            "mediaVolume": 0.5,
            "mediaDistanceModel": "inverse",
            "mediaRolloffFactor": 2,
            "mediaRefDistance": 1,
            "mediaMaxDistance": 10000,
            "mediaConeInnerAngle": 360,
            "mediaConeOuterAngle": 0,
            "mediaConeOuterGain": 0
          }
        });
      });

      it('can export environment-settings', function () {
        let gltfPath = path.resolve(outDirPath, 'environment-settings.gltf');
        const asset = JSON.parse(fs.readFileSync(gltfPath));

        assert.strictEqual(asset.extensionsUsed.includes('MOZ_hubs_components'), true);
        assert.strictEqual(utils.checkExtensionAdded(asset), true);

        const scene = asset.scenes[0];
        assert.strictEqual(utils.checkExtensionAdded(scene), true);

        const ext = scene.extensions['MOZ_hubs_components'];
        assert.deepStrictEqual(ext, {
          "environment-settings": {
            "toneMapping": "LUTToneMapping",
            "toneMappingExposure": 1,
            "backgroundColor": "#ffffff",
            "backgroundTexture": {
              "__mhc_link_type": "texture",
              "index": 0
            },
            "envMapTexture": {
              "__mhc_link_type": "texture",
              "index": 1
            }
          }
        });
      });
    });
  });
});