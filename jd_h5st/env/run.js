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

const consoleOutput = [];
const sandbox = {
  console: {
    log: (...a) => consoleOutput.push(['log', ...a]),
    info: (...a) => consoleOutput.push(['info', ...a]),
    warn: (...a) => consoleOutput.push(['warn', ...a]),
    error: (...a) => consoleOutput.push(['error', ...a])
  },
  setTimeout: (fn, delay) => 0,
  setInterval: (fn, delay) => 0,
  clearTimeout: () => {},
  clearInterval: () => {},
  atob: (str) => Buffer.from(str, 'base64').toString('binary'),
  btoa: (str) => Buffer.from(str, 'binary').toString('base64'),
  XMLHttpRequest: class XMLHttpRequest {
    open() {}
    send() {}
    setRequestHeader() {}
    getResponseHeader() { return null; }
    getAllResponseHeaders() { return ''; }
    addEventListener() {}
    removeEventListener() {}
  }
};
sandbox.window = sandbox;
sandbox.global = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
const context = vm.createContext(sandbox);

function load(file) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file, timeout: 30000 });
}

load(path.join(envRoot, 'core', 'ProxyMonitor.js'));
for (const mod of modules) load(path.join(envRoot, mod));
load(target);

const result = vm.runInContext(`(() => {
  const errors = [];
  const sdk = new window.ParamsSign({
    appId: 'f06cc',
    preRequest: false,
    onSign: (v) => { if (v && v.code !== 0) errors.push(v); },
    onRequestTokenRemotely: (v) => { if (v && v.code !== 200) errors.push(v); }
  });
  const input = {
    appid: 'search-pc-java',
    functionId: 'pc_search_searchWare',
    client: 'pc',
    clientVersion: '1.0.0',
    t: 1788577239831,
    body: 'fixture-body-sha256'
  };
  const before = {
    appId: sdk._appId,
    version: sdk._version,
    isNormal: sdk._isNormal,
    tokenLength: sdk._token.length,
    fingerprintLength: sdk._fingerprint.length,
    algorithms: Object.keys(sdk._algos)
  };
  let output;
  let thrown = null;
  try { output = sdk.signSync(input); } catch (e) { thrown = String(e); }
  return {
    before,
    outputType: typeof output,
    outputKeys: output && typeof output === 'object' ? Object.keys(output) : [],
    outputSummary: output && typeof output === 'object' ? {
      h5stType: typeof output.h5st,
      h5stLength: output.h5st ? String(output.h5st).length : 0,
      h5stSegments: output.h5st ? String(output.h5st).split(';').length : 0
    } : null,
    thrown,
    errors
  };
})()`, context);

console.log(JSON.stringify({ result, consoleOutput }, null, 2));
