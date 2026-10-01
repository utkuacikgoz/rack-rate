/* Pure workload calculations shared by the page and regression tests. */
(function (root) {
  function eligible(pair, options) {
    return options.plans.includes(pair.plan_id) &&
      (pair.region !== 'china' || options.region === 'china') &&
      (options.exploratory || (pair.access_status !== 'unverified' && pair.confidence !== 'low'));
  }
  function costs(pair, tasks) {
    if (!Number.isFinite(tasks) || tasks <= 0) return null;
    const monthly = pair.price_usd_month;
    return { monthly, perTask: monthly / tasks, apiMonthly: pair.api_cost_per_task_usd * tasks,
      breakEven: Math.ceil(monthly / pair.api_cost_per_task_usd),
      capacity: pair.tasks_per_month, fits: tasks <= pair.tasks_per_month };
  }
  function recommend(models, pairs, options) {
    if (!(options.tasks > 0) || !(options.budget > 0)) return [];
    const candidates = models.filter(m => m.api_cost_per_task_usd * options.tasks <= options.budget)
      .map(m => ({ model_id: m.id, model_name: m.name, score_pct: m.score_pct,
        plan_id: 'api', plan_name: 'API list estimate', monthly: m.api_cost_per_task_usd * options.tasks,
        perTask: m.api_cost_per_task_usd, access_status: 'benchmark', confidence: 'benchmark' }));
    pairs.filter(p => eligible(p, options)).forEach(p => {
      const c = costs(p, options.tasks);
      if (c.fits && c.monthly <= options.budget) candidates.push({ ...p, ...c });
    });
    candidates.sort((a, b) => b.score_pct - a.score_pct || a.monthly - b.monthly || a.plan_id.localeCompare(b.plan_id));
    // Offer distinct models as alternatives, choosing the least expensive route for each.
    return candidates.filter((p, i) => candidates.findIndex(x => x.model_id === p.model_id) === i);
  }
  const api = { eligible, costs, recommend };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RackRateDecision = api;
})(typeof window !== 'undefined' ? window : globalThis);
