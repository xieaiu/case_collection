const fs = require('node:fs');
const path = require('node:path');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;
const t = require('@babel/types');

const root = path.resolve(__dirname, '..');
const input = path.join(root, 'intermediate', 'js_security_v3_0.1.6.step2_runtime_strings.js');
const output = path.join(root, 'source', 'deobfuscated', 'js_security_v3_0.1.6.readable.js');
const reportPath = path.join(root, 'intermediate', 'js_security_v3_0.1.6.report.json');

function parse(source) {
  return parser.parse(source, {
    sourceType: 'script',
    allowReturnOutsideFunction: true,
    plugins: ['asyncGenerators', 'classProperties', 'objectRestSpread', 'optionalChaining', 'nullishCoalescingOperator']
  });
}

function literalValue(node) {
  if (t.isNumericLiteral(node) || t.isStringLiteral(node) || t.isBooleanLiteral(node) || t.isNullLiteral(node)) return node.value;
  return undefined;
}

function foldBinary(node) {
  const left = literalValue(node.left);
  const right = literalValue(node.right);
  if (left === undefined || right === undefined) return { foldable: false };
  let result;
  try {
    switch (node.operator) {
      case '+': result = left + right; break;
      case '-': result = left - right; break;
      case '*': result = left * right; break;
      case '/': result = left / right; break;
      case '%': result = left % right; break;
      case '**': result = left ** right; break;
      case '<<': result = left << right; break;
      case '>>': result = left >> right; break;
      case '>>>': result = left >>> right; break;
      case '|': result = left | right; break;
      case '&': result = left & right; break;
      case '^': result = left ^ right; break;
      case '==': result = left == right; break;
      case '===': result = left === right; break;
      case '!=': result = left != right; break;
      case '!==': result = left !== right; break;
      case '<': result = left < right; break;
      case '<=': result = left <= right; break;
      case '>': result = left > right; break;
      case '>=': result = left >= right; break;
      default: return { foldable: false };
    }
  } catch (_) {
    return { foldable: false };
  }
  return { foldable: true, value: result };
}

function toLiteral(value) {
  if (typeof value === 'string') return t.stringLiteral(value);
  if (typeof value === 'number' && Number.isFinite(value)) return t.numericLiteral(value);
  if (typeof value === 'boolean') return t.booleanLiteral(value);
  if (value === null) return t.nullLiteral();
  return null;
}

const source = fs.readFileSync(input, 'utf8');
const ast = parse(source);
let binaryFolded = 0;
let unaryFolded = 0;
let memberNormalized = 0;

for (let round = 0; round < 3; round += 1) {
  traverse(ast, {
    BinaryExpression(path) {
      const folded = foldBinary(path.node);
      if (!folded.foldable) return;
      const replacement = toLiteral(folded.value);
      if (replacement) {
        path.replaceWith(replacement);
        binaryFolded += 1;
      }
    },
    UnaryExpression(path) {
      const value = literalValue(path.node.argument);
      if (value === undefined) return;
      let result;
      switch (path.node.operator) {
        case '+': result = +value; break;
        case '-': result = -value; break;
        case '~': result = ~value; break;
        case '!': result = !value; break;
        default: return;
      }
      const replacement = toLiteral(result);
      if (replacement) {
        path.replaceWith(replacement);
        unaryFolded += 1;
      }
    },
    MemberExpression(path) {
      if (!path.node.computed || !t.isStringLiteral(path.node.property)) return;
      if (!/^[$A-Z_a-z][$0-9A-Z_a-z]*$/.test(path.node.property.value)) return;
      path.node.computed = false;
      path.node.property = t.identifier(path.node.property.value);
      memberNormalized += 1;
    }
  });
}

const result = generate(ast, {
  comments: false,
  compact: false,
  jsescOption: { minimal: true }
}, source).code + '\n';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, result);
const reparsed = parse(result);
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
report.pipeline.push('restore a03438dp/mj runtime string decoder calls in isolated VM');
report.pipeline.push('conservative numeric/string/boolean constant folding');
report.stats.runtimeStringsRestored = 263;
report.stats.binaryFolded = binaryFolded;
report.stats.unaryFolded = unaryFolded;
report.stats.memberNormalized = memberNormalized;
report.stats.finalOutputChars = result.length;
report.stats.finalOutputLines = result.split(/\r?\n/).length;
report.artifacts.runtimeStrings = 'intermediate\\js_security_v3_0.1.6.step2_runtime_strings.js';
report.artifacts.readable = 'source\\deobfuscated\\js_security_v3_0.1.6.readable.js';
report.residual.push('The second-layer string decoder is now resolved, but VM dispatch remains bytecode-driven.');
report.residual.push('The final reading artifact was reparsed successfully after constant folding.');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ ...report.stats, syntax: 'ok', output }, null, 2));
