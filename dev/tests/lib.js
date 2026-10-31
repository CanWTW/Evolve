const E = window.__evolve, C = E.core, D = C.DATA;
const WB = { sword: 'base.rift_blade', axe: 'base.iron_axe', mace: 'base.war_mace', bow: 'base.hunter_bow', darts: 'base.throwing_darts', pistol: 'base.flint_pistol' };
const G = C.GEM_IDS; const ids = Array.isArray(G) ? G : Object.values(G).flat();
const actives = ids.filter((i) => C.gemType(i) === 'active' && D.SKILLS[i].kind !== 'buff');
const sups = ids.filter((i) => C.gemType(i) === 'support');
function run(spec, opt) {
  opt = opt || {};
  E.newRun(opt.seed || 11, 'zone.rift_outskirts'); E.setFrozen(true); const g = E.game; g.noSpawns = true; g.godMode = !opt.mortal; g.autoMove = true;
  C.setCharacterLevel(g, 30);
  const sk = D.SKILLS[spec.mains[0].skill]; const cls = opt.weapon || (sk && sk.weapons ? sk.weapons[0] : null);
  if (cls) { const it = C.rollItem(g, 'common', 'weapon', { ilvl: 1 }); it.base = WB[cls]; it.affixes = []; it.unique = null; it.special = null; it.name = C.itemName(it); g.player.equip.weapon = it; }
  C.setBuild(g, spec); C.normalizeBuild(g); C.recomputeStats(g); if (opt.setup) opt.setup(g);
  g.enemies.length = 0; const p = g.player; p.x = 320; p.y = 180;
  const n = opt.n || (opt.cluster ? 12 : 8);
  for (let i = 0; i < n; i++) { const a = opt.cluster ? (i % 4 - 1.5) * 0.18 : i / n * Math.PI * 2, r = opt.cluster ? 90 + Math.floor(i / 4) * 22 : 26 + (i % 3) * 30; const e = C.spawnEnemy(g, opt.enemy || 'enemy.chaser', p.x + Math.cos(a) * r, p.y + Math.sin(a) * r, { force: true }); if (e && !opt.realHp) { e.maxHp = e.hp = 1e8; e.speed = 0; e.spd = 0; e.baseSpeed = 0; } }
  const T = opt.secs || 6; let zonesMax = 0, minionsMax = 0;
  for (let i = 0; i < T * 60; i++) { C.step(g, opt.inputFn ? opt.inputFn(i, g) : (opt.input || {}), 1 / 60); zonesMax = Math.max(zonesMax, g.zones.length); minionsMax = Math.max(minionsMax, (g.minions || []).length); if (!opt.realHp) { for (const e of g.enemies) if (!e.dead && e.hp < 1e7) e.hp = 1e8; } else if (i % 60 === 0 && g.enemies.filter((e) => !e.dead).length < 6) { for (let k = 0; k < 4; k++) C.spawnEnemy(g, 'enemy.chaser', p.x + 30 + k * 10, p.y + 20, { force: true }); } }
  const S = g.stats; const dmg = Object.values(S.dmgBySource).reduce((a, b) => a + b, 0);
  return { dmg: Math.round(dmg), src: Object.fromEntries(Object.entries(S.dmgBySource).map(([k, v]) => [k, Math.round(v)])), casts: Object.values(S.casts || {}).reduce((a, b) => a + b, 0), zonesMax, minionsMax, st: Object.values(S.statusApplied).reduce((a, b) => a + b, 0), react: Object.values(S.reactions).reduce((a, b) => a + b, 0), trig: Object.values(S.triggers).reduce((a, b) => a + b, 0), trigs: S.triggers, links: g.player.build.links.map((L) => L.n || 0), blocks: S.blocks || 0, dodges: S.dodges, proj: S.maxPlayerProjInTick, hp: Math.round(p.hp) };
}
window.__audit = { run, actives, sups, ids };

return 1;