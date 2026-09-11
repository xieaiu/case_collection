const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const skillRoot = 'C:\\Users\\XIE\\.agents\\skills\\js-reverse\\env-patch';
const envRoot = path.join(skillRoot, 'env');
const target = path.join(root, 'source', 'deobfuscated', 'js_security_v3_0.1.6.readable.js');
const modules = [
  'bom/navigator.js', 'bom/location.js', 'bom/screen.js', 'bom/storage.js',
  'bom/window.js', 'bom/crypto.js', 'bom/performance.js',
  'dom/event.js', 'dom/document.js', 'dom/elements.js',
  'webapi/blob.js', 'webapi/url.js', 'encoding/textencoder.js'
];

function createSdk(seed = {}) {
  const sandbox = {
    console: { log() {}, info() {}, warn() {}, error() {} },
    setTimeout: () => 0, setInterval: () => 0,
    clearTimeout() {}, clearInterval() {},
    atob: (str) => Buffer.from(str, 'base64').toString('binary'),
    btoa: (str) => Buffer.from(str, 'binary').toString('base64'),
    XMLHttpRequest: class XMLHttpRequest {
      open() {} send() {} setRequestHeader() {}
      getResponseHeader() { return null; }
      getAllResponseHeaders() { return ''; }
      addEventListener() {} removeEventListener() {}
    }
  };
  sandbox.window = sandbox;
  sandbox.global = sandbox;
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  const context = vm.createContext(sandbox);
  const load = (file) => vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file, timeout: 30000 });
  load(path.join(envRoot, 'core', 'ProxyMonitor.js'));
  for (const mod of modules) load(path.join(envRoot, mod));
  load(target);
  const sdk = vm.runInContext(`new window.ParamsSign({appId:'f06cc',preRequest:false})`, context);
  if (typeof seed.token === 'string' && seed.token.length > 0) sdk._token = seed.token;
  if (typeof seed.fingerprint === 'string' && seed.fingerprint.length > 0) sdk._fingerprint = seed.fingerprint;
  if (seed.isNormal === true) sdk._isNormal = true;
  return { sdk, context };
}

function sign(input, seed) {
  if (!input || typeof input !== 'object') throw new TypeError('input must be an object');
  const { sdk } = createSdk(seed);
  return sdk.signSync({ ...input });
}

module.exports = { sign };

if (require.main === module) {
  const input = JSON.parse(process.argv[2] || '{}');
  const seed = {
    token: process.env.JD_H5ST_TOKEN || '',
    fingerprint: process.env.JD_H5ST_FINGERPRINT || '',
    isNormal: process.env.JD_H5ST_IS_NORMAL === '1'
  };
  const result = sign(input, seed);
  process.stdout.write(JSON.stringify({
    output: result,
    summary: {
      h5stLength: result && result.h5st ? String(result.h5st).length : 0,
      h5stSegments: result && result.h5st ? String(result.h5st).split(';').length : 0
    }
  }));
}
