const fs = require('fs');
const glob = require('glob')
const path = require('path');
const { test } = require('./tests/link.js');
const utils = require('./utils.js');

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

const basePath = path.join(__dirname);
const tests = glob.sync(path.join(basePath, 'tests', '*.js')).reduce((loaded, file) => {
  const mod = require('./' + path.relative(basePath, file));
  loaded.push(mod);
  return loaded;
}, []);

describe('Exporter', function () {
  const blenderSampleScenes = fs.readdirSync('scenes').filter(f => f.endsWith('.blend')).map(f => f.substring(0, f.length - 6));

  blenderVersions.forEach(function (blenderVersion) {
    let variants = [
      ['', '']
    ];

    variants.forEach(function (variant) {
      const args = variant[1];
      describe(blenderVersion + '_export' + variant[0], function () {
        blenderSampleScenes.forEach((scene) => {
          it(scene, function (done) {
            let outDirName = 'out' + blenderVersion + variant[0];
            let blenderPath = `scenes/${scene}.blend`;
            let ext = args.indexOf('--glb') === -1 ? '.gltf' : '.glb';
            let outDirPath = path.resolve(OUT_PREFIX, outDirName, 'export');
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
      let outDirPath = path.resolve(OUT_PREFIX, outDirName, 'export');

      tests.forEach(test => {
        it(test.description, () => test.test(outDirPath));
      });
    });
  });
});

describe('Importer / Exporter (Roundtrip)', function () {
  const blenderSampleScenes = fs.readdirSync('scenes').filter(f => f.endsWith('.blend')).map(f => f.substring(0, f.length - 6));

  blenderVersions.forEach(function (blenderVersion) {
    let variants = [
      ['', '']
    ];

    variants.forEach(function (variant) {
      const args = variant[1];
      describe(blenderVersion + '_roundtrip' + variant[0], function () {
        blenderSampleScenes.forEach(scene => {
          it(scene, function (done) {
            let outDirName = 'out' + blenderVersion + variant[0];
            let ext = args.indexOf('--glb') === -1 ? '.gltf' : '.glb';
            let exportSrcPath = path.resolve(OUT_PREFIX, outDirName, 'export');
            let gltfSrcPath = path.resolve(exportSrcPath, `${scene}${ext}`);
            let outDirPath = path.resolve(OUT_PREFIX, outDirName, 'roundtrip');
            let gltfDstPath = path.resolve(outDirPath, `${scene}${ext}`);
            let options = args;

            utils.blenderRoundtripGltf(blenderVersion, gltfSrcPath, outDirPath, (error) => {
              if (error)
                return done(error);

              utils.validateGltf(gltfSrcPath, (error, gltfSrcReport) => {
                if (error)
                  return done(error);

                utils.validateGltf(gltfDstPath, (error, gltfDstReport) => {
                  if (error)
                    return done(error);

                  let reduceKeys = function (raw, allowed) {
                    return Object.keys(raw)
                      .filter(key => allowed.includes(key))
                      .reduce((obj, key) => {
                        obj[key] = raw[key];
                        return obj;
                      }, {});
                  };

                  done();
                });
              });
            }, options);
          });
        });
      });
    });

    describe(blenderVersion + '_roundtrip_results', function () {
      let outDirName = 'out' + blenderVersion;
      let outDirPath = path.resolve(OUT_PREFIX, outDirName, 'roundtrip');

      tests.forEach(test => {
        it(test.description, () => test.test(outDirPath));
      });
    });
  });
});