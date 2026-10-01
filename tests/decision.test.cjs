const { test } = require('node:test');
const assert = require('node:assert/strict');
const { eligible, costs, recommend } = require('../site/decision.js');
const pair = { model_id: 'cheap', model_name: 'Cheap', score_pct: 60, plan_id: 'pro', plan_name: 'Pro',
  price_usd_month: 20, api_cost_per_task_usd: .1, tasks_per_month: 600,
  access_status: 'observed', region: 'check_vendor', confidence: 'measured' };
const model = { id: 'cheap', name: 'Cheap', score_pct: 60, api_cost_per_task_usd: .1 };
const options = { plans: ['pro'], region: 'other', exploratory: false, tasks: 10, budget: 20 };
test('light usage favors API; subscription wins after break-even', () => {
  assert.equal(costs(pair, 10).perTask, 2);
  assert.equal(recommend([model], [pair], options)[0].plan_id, 'api');
  assert.equal(recommend([model], [pair], {...options, tasks: 300, budget: 30})[0].plan_id, 'pro');
});
test('over-quota workloads never get presented as covered by the monthly price', () => {
  assert.equal(costs(pair, 601).fits, false);
  assert.deepEqual(recommend([model], [pair], {...options, tasks: 601}), []);
});
test('unverified access, low confidence and China-only plans require explicit eligibility', () => {
  assert.equal(eligible({...pair, access_status: 'unverified'}, options), false);
  assert.equal(eligible({...pair, confidence: 'low'}, options), false);
  assert.equal(eligible({...pair, region: 'china'}, options), false);
  assert.equal(eligible({...pair, access_status: 'unverified'}, {...options, exploratory: true}), true);
  assert.equal(eligible({...pair, region: 'china'}, {...options, region: 'china'}), true);
});
test('invalid workload has no fabricated price', () => {
  assert.equal(costs(pair, 0), null);
  assert.equal(costs(pair, NaN), null);
});
