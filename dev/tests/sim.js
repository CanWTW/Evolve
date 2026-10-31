const E = window.__evolve, C = E.core, D = C.DATA; const { actives } = window.__audit;
const WB = { sword: 'base.rift_blade', axe: 'base.iron_axe', mace: 'base.war_mace', bow: 'base.hunter_bow', darts: 'base.throwing_darts', pistol: 'base.flint_pistol' };
const LV = window.__simLv || 12, ZONE = window.__simZone || 'zone.rift_outskirts', SECS = window.__simSecs || 90;
function sim(mains, seed, wcls) {
  E.newRun(seed, ZONE); const g = E.game; g.godMode = true; C.setCharacterLevel(g, LV);
  if (wcls) { const it = C.rollItem(g, 'common', 'weapon', { ilvl: 1 }); it.base = WB[wcls]; it.affixes = []; it.unique = null; it.special = null; it.name = C.itemName(it); g.player.equip.weapon = it; }
  C.setBuild(g, { mains, layout: 3 }); C.normalizeBuild(g); C.recomputeStats(g); g.evoPaths = {}; E.setFrozen(true); g.noBoons = true;
  for (let i = 0; i < 60 * SECS && g.state === 'playing'; i++) C.step(g, C.autopilot(g), 1 / 60);
  const dmg = Object.values(g.stats.dmgBySource).reduce((a, b) => a + b, 0); return { dps: dmg / g.t, kills: g.stats.kills };
}
const out = {};
const list = window.__simList || actives.filter((a) => !C.isMoveSkill(a));
for (const a of list) {
  const sk = D.SKILLS[a]; const w = sk.weapons ? sk.weapons[0] : null; let dps = 0, k = 0;
  for (const sd of (window.__seeds || [3, 7, 11])) { const r = sim([{ skill: a, sup: [] }], sd, w); dps += r.dps / 3; k += r.kills / 3; }
  out[a] = { dps: Math.round(dps), kills: Math.round(k), cat: sk.kind === 'summon' ? 'minion' : sk.attack ? (['bow', 'darts', 'pistol'].includes(w) ? 'ranged' : 'melee') : 'spell' };
}
return out;
