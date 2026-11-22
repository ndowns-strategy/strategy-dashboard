// Records what strategy-dashboard-client.js sends for each case in tests/cases.json and writes tests/golden.json.
// The Python port must send exactly the same thing (tests/test_parity.py). Run: node tests/harness.js
// Network calls are stubbed: taskProc returns tests/fixtures/server.json (or {"bs":"BS1"} for edits), /api returns {}.
// Date.now and crypto.getRandomValues are fixed so the output is repeatable; the Python test uses the same values.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'strategy-dashboard-client.js'), 'utf8');
const server = fs.readFileSync(path.join(__dirname, 'fixtures', 'server.json'), 'utf8');
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, 'cases.json'), 'utf8'));

let log = [];
let keyCounter = 0;
const fakeFetch = async (url, opts = {}) => {
  let text;
  if (url.endsWith('/servlet/taskProc')) {
    const p = Object.fromEntries(new URLSearchParams(opts.body));
    if (p.taskId === 'mojoRWManipulation') {
      const params = JSON.parse(p.params);
      log.push({ edit: { actions: params.actions, nodes: params.partialRetrieval.nodes, rwb: p.rwb } });
      text = '{"bs":"BS1"}';
    } else {
      log.push({ task: p.taskId, excludeData: p.excludeData });
      text = server;
    }
  } else {
    log.push({ api: opts.method, path: url.replace('/MicroStrategyLibrary/api', ''), body: opts.body ? JSON.parse(opts.body) : null });
    text = '{"id":"NEW","mid":"MID"}';
  }
  return { ok: true, status: 200, text: async () => text, headers: { get: () => null } };
};

const ctx = vm.createContext({
  fetch: fakeFetch, URLSearchParams, btoa, console,
  crypto: { getRandomValues: (a) => { for (let i = 0; i < a.length; i++) a[i] = (keyCounter * 16 + i) & 255; keyCounter++; return a; } },
  window: {}, XMLHttpRequest: function () {}, Headers: function () {},
});
vm.runInContext(src + `
Date.now = () => 1763800000000;
globalThis.__client = client;`, ctx);

(async () => {
  const out = {};
  for (const c of cases) {
    log = []; keyCounter = 0;
    const cl = ctx.__client('TOKEN', 'PROJECT');
    const s = await cl.open('DASH');
    log = [];
    const args = [...(c.args || []), ...(c.opts ? [c.opts] : [])];
    let result;
    try { result = await s[c.js](...args); } catch (e) { result = { error: String(e.message || e) }; }
    out[c.name] = { calls: log, result: typeof result === 'string' ? null : result ?? null };
  }
  fs.writeFileSync(path.join(__dirname, 'golden.json'), JSON.stringify(out, null, 1) + '\n');
  console.log(`wrote ${Object.keys(out).length} cases to tests/golden.json`);
})();
