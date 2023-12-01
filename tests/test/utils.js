const fs = require('fs');
const path = require('path');
const validator = require('gltf-validator');

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function blenderFileToGltf(blenderVersion, blenderPath, outDirName, done, options = '') {
  const { exec } = require('child_process');
  const cmd = `BLENDER_USER_SCRIPTS=${path.resolve("../")} ${blenderVersion} -b --factory-startup --addons io_hubs_addon -noaudio ${blenderPath} --python export_gltf.py -- ${outDirName} ${options}`;
  var prc = exec(cmd, (error, stdout, stderr) => {
    //if (stderr) process.stderr.write(stderr);

    if (error) {
      console.log(stdout);
      done(error);
      return;
    }
    done();
  });
}

function blenderRoundtripGltf(blenderVersion, gltfPath, outDirName, done, options = '') {
  const { exec } = require('child_process');
  const cmd = `BLENDER_USER_SCRIPTS=${path.resolve("../")} ${blenderVersion} -b --factory-startup --addons io_hubs_addon -noaudio --python roundtrip_gltf.py -- ${gltfPath} ${outDirName} ${options}`;
  var prc = exec(cmd, (error, stdout, stderr) => {
    //if (stderr) process.stderr.write(stderr);

    if (error) {
      done(error);
      return;
    }
    done();
  });
}

function validateGltf(gltfPath, done) {
  const asset = fs.readFileSync(gltfPath);
  validator.validateBytes(new Uint8Array(asset), {
    uri: gltfPath,
    externalResourceFunction: (uri) =>
      new Promise((resolve, reject) => {
        uri = path.resolve(path.dirname(gltfPath), decodeURIComponent(uri));
        // console.info("Loading external file: " + uri);
        fs.readFile(uri, (err, data) => {
          if (err) {
            console.error(err.toString());
            reject(err.toString());
            return;
          }
          resolve(data);
        });
      })
  }).then((result) => {
    // [result] will contain validation report in object form.
    if (result.issues.numErrors > 0) {
      const errors = result.issues.messages.filter(i => i.severity === 0)
        .reduce((msg, i, idx) => (idx > 5) ? msg : `${msg}\n${i.pointer} - ${i.message} (${i.code})`, '');
      done(new Error("Validation failed for " + gltfPath + '\nFirst few messages:' + errors), result);
      return;
    }
    done(null, result);
  }, (result) => {
    // Promise rejection means that arguments were invalid or validator was unable
    // to detect file format (glTF or GLB).
    // [result] will contain exception string.
    done(result);
  });
}

function checkExtensionAdded(asset, etxName) {
  return Object.prototype.hasOwnProperty.call(asset.extensions, etxName);
}

function nodeWithName(gltf, name) {
  const node = gltf.nodes.filter(node => { return node.name === name; }).pop();
  const index = gltf.nodes.indexOf(node);
  return {
    node,
    index
  };
}

function materialWithName(gltf, name) {
  const node = gltf.materials.filter(node => { return node.name === name; }).pop();
  const index = gltf.nodes.indexOf(node);
  return {
    node,
    index
  };
}

exports.utils = {
  UUID_REGEX,
  blenderFileToGltf,
  blenderRoundtripGltf,
  validateGltf,
  checkExtensionAdded,
  nodeWithName,
  materialWithName
};