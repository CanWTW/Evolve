const E = window.__evolve, C = E.core, D = C.DATA; const { run, actives, sups } = window.__audit;
const out = { base: {}, sup: {} };
for (const a of actives) {
  const b = run({ mains: [{ skill: a, sup: [] }] }); out.base[a] = b;
  for (const s of sups) { if (!(C.supportOk ? C.supportOk(s, a, [s]) : C.supportApplies(s, a))) continue; const r = run({ mains: [{ skill: a, sup: [s] }] }); out.sup[a + '|' + s] = r; }
}
return out;
