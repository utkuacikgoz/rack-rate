const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
function page(hash = '') {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', e => errors.push(e.message));
  const dom = new JSDOM(fs.readFileSync('site/index.html', 'utf8'), {
    url: 'https://rack-rate.example/' + hash, runScripts: 'dangerously',
    pretendToBeVisual: true, virtualConsole,
    beforeParse(w) {
      w.RackRateDecision = require("../site/decision.js");
      w.matchMedia = () => ({ matches: true });
      w.SVGElement.prototype.getBBox = () => ({ x: 0, y: 0, width: 80, height: 14 });
      w.HTMLElement.prototype.scrollTo = () => {};
    }
  });
  assert.deepEqual(errors, [], 'page must initialize without script errors');
  return dom;
}
test('budget recommendation opens the same plan, including after reload', () => {
  const dom = page();
  const d = dom.window.document;
  assert.match(d.querySelector('#budget-result').textContent, /ChatGPT Plus/);
  d.querySelector('#budget-result button').click();
  assert.match(d.querySelector('#rail-content').textContent, /\$20 \/ /);
  assert.doesNotMatch(d.querySelector('#rail-content').textContent, /ChatGPT Pro 20x/);
  const reloaded = page(dom.window.location.hash);
  assert.match(reloaded.window.document.querySelector('#rail-content').textContent, /ChatGPT Plus/);
  reloaded.window.close(); dom.window.close();
});
test('plan filters apply to table, runtime and model details', () => {
  const dom = page('#plans=chatgpt-plus&model=gpt-5.6-sol');
  const d = dom.window.document;
  assert.match(d.querySelector('#rail-content').textContent, /ChatGPT Plus/);
  assert.doesNotMatch(d.querySelector('#runtime-svg').textContent, /Pro 20x/);
  assert.doesNotMatch(d.querySelector('#routes-body').textContent, /Pro 20x/);
  dom.window.close();
});
test('empty plan selection survives reload', () => {
  const dom = page('#plans=');
  assert.match(dom.window.document.querySelector('#routes-body').textContent, /No priced routes/);
  dom.window.close();
});
test('all local navigation targets exist in the deployed directory', () => {
  const dom = page();
  for (const a of dom.window.document.querySelectorAll('a[href]')) {
    const href = a.getAttribute('href');
    if (href.startsWith('#')) assert.ok(dom.window.document.getElementById(href.slice(1)), href);
    else if (!/^[a-z]+:/i.test(href)) assert.ok(fs.existsSync(path.join('site', href)), href);
  }
  dom.window.close();
});
test('workload and eligibility survive recommendation share links', () => {
  const dom = page('#tasks=1&budget=1&region=china&exploratory=1');
  const d = dom.window.document;
  assert.match(d.querySelector('#budget-result').textContent, /API list estimate/);
  assert.equal(d.querySelector('#tasks-input').value, '1');
  d.querySelector('#budget-result button').click();
  const reloaded = page(dom.window.location.hash);
  assert.match(reloaded.window.document.querySelector('#rail-content').textContent, /API list estimate/);
  assert.equal(reloaded.window.document.querySelector('#region-input').value, 'china');
  assert.equal(reloaded.window.document.querySelector('#exploratory-input').checked, true);
  reloaded.window.close(); dom.window.close();
});
test('unverified model access is not shown as an eligible plan by default', () => {
  const dom = page('#plans=ollama-pro');
  assert.match(dom.window.document.querySelector('#routes-body').textContent, /No priced routes/);
  dom.window.document.querySelector('#exploratory-input').checked = true;
  dom.window.document.querySelector('#exploratory-input').dispatchEvent(new dom.window.Event('input'));
  assert.match(dom.window.document.querySelector('#routes-body').textContent, /Ollama Pro/);
  dom.window.close();
});
