const fs = require('node:fs');
const path = require('node:path');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;
const t = require('@babel/types');

const root = path.resolve(__dirname, '..');
const input = path.join(root, 'reverse-records', 'js_security_v3_0.1.6.original.js');
const intermediateDir = path.join(root, 'intermediate');
const outputDir = path.join(root, 'source', 'deobfuscated');
const step1 = path.join(intermediateDir, 'js_security_v3_0.1.6.step1_strings.js');
const output = path.join(outputDir, 'js_security_v3_0.1.6.readable.js');
const reportPath = path.join(root, 'intermediate', 'js_security_v3_0.1.6.report.json');

function parse(source) {
  return parser.parse(source, {
    sourceType: 'script',
    allowReturnOutsideFunction: true,
    allowAwaitOutsideFunction: true,
    errorRecovery: false,
    plugins: [
      'asyncGenerators', 'classProperties', 'objectRestSpread',
      'optionalCatchBinding', 'optionalChaining', 'nullishCoalescingOperator'
    ]
  });
}

function decodeXor5(value) {
  let out = '';
  for (let i = 0; i < value.length;) {
    const c = value.charCodeAt(i++);
    if (c > 63) out += String.fromCharCode(c ^ 5);
    else if (c === 35) out += value.charAt(i++);
    else out += String.fromCharCode(c);
  }
  return out;
}

function isDecoderCall(node) {
  return t.isCallExpression(node)
    && t.isIdentifier(node.callee, { name: '_4vve5' })
    && node.arguments.length === 1
    && t.isStringLiteral(node.arguments[0]);
}

function countNodes(ast, type) {
  let count = 0;
  traverse(ast, { [type]() { count += 1; } });
  return count;
}

const source = fs.readFileSync(input, 'utf8');
const ast = parse(source);
const stats = {
  inputChars: source.length,
  inputLines: source.split(/\r?\n/).length,
  decoderCallsBefore: countNodes(ast, 'CallExpression'),
  stringRestored: 0,
  whileStatements: countNodes(ast, 'WhileStatement'),
  switchStatements: countNodes(ast, 'SwitchStatement'),
  vmBytecodeArrays: 0
};

traverse(ast, {
  CallExpression(path) {
    if (!isDecoderCall(path.node)) return;
    path.replaceWith(t.stringLiteral(decodeXor5(path.node.arguments[0].value)));
    stats.stringRestored += 1;
  },
  VariableDeclarator(path) {
    if (t.isIdentifier(path.node.id, { name: '_2hoe5' }) && t.isArrayExpression(path.node.init)) {
      stats.vmBytecodeArrays += 1;
    }
  }
});

const first = generate(ast, {
  comments: false,
  compact: false,
  jsescOption: { minimal: true }
}, source).code + '\n';
fs.mkdirSync(intermediateDir, { recursive: true });
fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(step1, first);

// Reparse the generated artifact before producing the reading copy.
const reparsed = parse(first);
traverse(reparsed, {
  MemberExpression(path) {
    if (!path.node.computed || !t.isStringLiteral(path.node.property)) return;
    if (!/^[$A-Z_a-z][$0-9A-Z_a-z]*$/.test(path.node.property.value)) return;
    path.node.computed = false;
    path.node.property = t.identifier(path.node.property.value);
  }
});
const readable = generate(reparsed, {
  comments: false,
  compact: false,
  jsescOption: { minimal: true }
}, first).code + '\n';
fs.writeFileSync(output, readable);

const report = {
  family: 'custom stack-machine / VM-style mixed obfuscation',
  pipeline: [
    'parse with Babel',
    'restore _4vve5 XOR-5 string decoder calls',
    'generate intermediate artifact',
    'reparse',
    'normalize safe computed member access'
  ],
  stats: {
    ...stats,
    outputChars: readable.length,
    outputLines: readable.split(/\r?\n/).length,
    decoderCallsAfter: countNodes(reparsed, 'CallExpression')
  },
  entryPoints: {
    publicAsync: 'ParamsSign.prototype.sign',
    publicSync: 'ParamsSign.prototype.signSync',
    vmEntry: 'ParamsSign.prototype._$sdnmd',
    tokenRefresh: 'ParamsSign.prototype._$ram'
  },
  residual: [
    'The _2hoe5 bytecode array and _$sdnmd stack machine remain intact.',
    'Runtime fingerprint/token state is not statically evaluated.',
    'No algorithm or browser-environment emulation was attempted.'
  ],
  artifacts: {
    original: path.relative(root, input),
    intermediate: path.relative(root, step1),
    readable: path.relative(root, output)
  }
};
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
