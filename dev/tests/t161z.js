const E = window.__evolve, C = E.core, R = {};
const fresh = (mains) => { E.newRun(5, window.__Z || 'zone.rift_outskirts'); const g = E.game; E.setFrozen(true); g.noSpawns = true; g.godMode = true; C.setCharacterLevel(g, window.__LV || 20); C.setBuild(g, { mains, layout: 3 }); C.normalizeBuild(g); C.recomputeStats(g); g.enemies.length = 0; return g; };
for (const id of ['skill.flame_dash', 'skill.lightning_warp', 'skill.frostblink']) {
  const g = fresh([{ skill: null, sup: [] }, { skill: id, sup: [] }]); const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 130, g.player.y, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0;
  for (let i = 0; i < 30; i++) C.step(g, {}, 1 / 60); const x0 = g.player.x; C.castMove(g, 1, 0);
  let frames = 0, hidden = 0, zonesMid = 0; while (g.player.motion && frames < 60) { frames++; if (g.player.motion.hide) hidden++; C.step(g, {}, 1 / 60); if (frames === Math.floor(frames) && g.player.motion && zonesMid < g.zones.length) zonesMid = g.zones.length; }
  R[id] = { frames, hidden, dx: Math.round(g.player.x - x0), dmg: Math.round(g.stats.dmgBySource[id] || 0), zonesMid, fx: [...new Set(g.fx.map((f) => f.type))].join(',') };
}
// fusion + banners + resonance pulse
const g = fresh([{ skill: 'skill.fireball', sup: [] }, { skill: null, sup: [] }, { skill: null, sup: [] }, { skill: 'skill.arc_spark', sup: [] }, { skill: null, sup: [] }, { skill: 'skill.chain_lightning', sup: [] }]); g.noSpawns = false;
let fusAt = null, firstBurst = null, banners = [];
for (let i = 0; i < 60 * 180 && g.state === 'playing'; i++) { C.step(g, C.autopilot(g), 1 / 60); if (g.banners && g.banners.length) { banners.push(...g.banners.map((b) => b.text)); g.banners.length = 0; } if (g.evo && g.evo.fusion && fusAt == null) fusAt = g.t; if ((g.stats.fusionCasts || 0) > 0 && firstBurst == null) firstBurst = g.t; if (firstBurst && g.t > firstBurst + 12) break; }
R.fusion = { fusAt: fusAt && Math.round(fusAt), firstBurst: firstBurst && +firstBurst.toFixed(1), casts: g.stats.fusionCasts, dmg: Math.round(Object.entries(g.stats.dmgBySource).filter(([k]) => k.startsWith('fusion')).reduce((s, [, v]) => s + v, 0)), total: Math.round(Object.values(g.stats.dmgBySource).reduce((s, v) => s + v, 0)), reso: g._reso, pulses: g.stats.resoPulses, resoDmg: Math.round(Object.entries(g.stats.dmgBySource).filter(([k]) => k.startsWith('reso')).reduce((s, [, v]) => s + v, 0)), stage: g.evo && g.evo.stage, banners };
return R;
