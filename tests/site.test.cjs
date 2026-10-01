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
test('comparison search and mobile sort preserve accurate route details', () => {
  const dom = page(); const d = dom.window.document;
  const search = d.querySelector('#route-search');
  search.value = 'ChatGPT'; search.dispatchEvent(new dom.window.Event('input'));
  assert.equal(d.querySelectorAll('#routes-body tr[data-model]').length, 1);
  d.querySelector('#routes-body button').click();
  assert.match(d.querySelector('#rail-content').textContent, /ChatGPT Plus/);
  d.querySelector('#rail-close').click();
  search.value = ''; search.dispatchEvent(new dom.window.Event('input'));
  const sort = d.querySelector('#route-sort'); sort.value = 'score_pct';
  sort.dispatchEvent(new dom.window.Event('change'));
  assert.equal(d.querySelector('#routes-body tr').dataset.model, 'gpt-5.6-sol');
  dom.window.close();
});
test('mobile comparisons expand and follow mode and evidence filters', () => {
  const dom = page(); const d = dom.window.document;
  assert.equal(d.querySelectorAll('#mobile-comparison .model-card').length, 5);
  d.querySelector('#mobile-comparison .text-action').click();
  assert.equal(d.querySelectorAll('#mobile-comparison .model-card').length, 28);
  d.querySelector('#toggle-pill button[data-mode="sub"]').click();
  assert.equal(d.querySelectorAll('#mobile-comparison .model-card').length, 3);
  assert.doesNotMatch(d.querySelector('#mobile-comparison').textContent, /Ollama/);
  dom.window.close();
});
test('modal traps focus, isolates background and restores the opener on Escape', () => {
  const dom = page(); const d = dom.window.document;
  const opener = d.querySelector('#budget-result button'); opener.focus(); opener.click();
  const rail = d.querySelector('#rail'), close = d.querySelector('#rail-close');
  assert.equal(rail.getAttribute('role'), 'dialog');
  assert.ok(d.querySelector('main').hasAttribute('inert'));
  assert.equal(d.activeElement, close);
  close.dispatchEvent(new dom.window.KeyboardEvent('keydown', {key:'Tab', shiftKey:true, bubbles:true, cancelable:true}));
  assert.equal(d.activeElement, [...rail.querySelectorAll('a[href], button:not([disabled])')].at(-1));
  d.dispatchEvent(new dom.window.KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
  assert.equal(d.activeElement, opener);
  assert.equal(d.querySelector('main').hasAttribute('inert'), false);
  assert.equal(rail.getAttribute('aria-hidden'), 'true');
  dom.window.close();
});
test('runtime and cross-check data have readable HTML text equivalents', () => {
  const dom = page(); const d = dom.window.document;
  assert.equal(d.querySelector('#runtime-svg').tagName, 'DIV');
  assert.equal(d.querySelectorAll('#runtime-svg .quota-card').length, 3);
  assert.equal(d.querySelectorAll('#cross-data .cross-card').length, 11);
  assert.match(d.querySelector('#cross-data').textContent, /Dollar conversion/);
  dom.window.close();
});
