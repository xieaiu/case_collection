const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;
const t = require('@babel/types');

const root = path.resolve(__dirname, '..');
const input = path.join(root, 'intermediate', 'js_security_v3_0.1.6.step1_strings.js');
const output = path.join(root, 'intermediate', 'js_security_v3_0.1.6.step2_runtime_strings.js');

function parse(source) {
  return parser.parse(source, {
    sourceType: 'script',
    allowReturnOutsideFunction: true,
    plugins: ['asyncGenerators', 'classProperties', 'objectRestSpread', 'optionalChaining', 'nullishCoalescingOperator']
  });
}

const source = fs.readFileSync(input, 'utf8');
const decoderStart = source.indexOf('function a03438dp');
const decoderEnd = source.indexOf('var mj = a03438dp,');
if (decoderStart < 0 || decoderEnd < 0 || decoderEnd <= decoderStart) {
  throw new Error('Could not isolate a03438dp decoder bootstrap');
}

// This slice contains only the local lookup table, its rotation IIFE, and the
// index/base64 decoder. It is deliberately not the full SDK.
const decoderSource = source.slice(decoderStart, decoderEnd);
const sandbox = { decodeURIComponent };
vm.createContext(sandbox);
vm.runInContext(`${decoderSource}\nthis.__decode = a03438dp;`, sandbox, { timeout: 1000 });

const ast = parse(source);
let restored = 0;
let failed = 0;
traverse(ast, {
  CallExpression(path) {
    const node = path.node;
    if (!t.isIdentifier(node.callee, { name: 'mj' }) || node.arguments.length !== 1) return;
    const arg = node.arguments[0];
    if (!t.isNumericLiteral(arg)) return;
    try {
      const value = sandbox.__decode(arg.value);
      if (typeof value !== 'string') return;
      path.replaceWith(t.stringLiteral(value));
      restored += 1;
    } catch (_) {
      failed += 1;
    }
  }
});

const result = generate(ast, {
  comments: false,
  compact: false,
  jsescOption: { minimal: true }
}, source).code + '\n';
fs.writeFileSync(output, result);
console.log(JSON.stringify({
  input: path.relative(root, input),
  output: path.relative(root, output),
  decoderChars: decoderSource.length,
  restored,
  failed,
  outputChars: result.length,
  outputLines: result.split(/\r?\n/).length
}, null, 2));
