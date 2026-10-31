const E = window.__evolve, C = E.core, D = C.DATA; const out = {};
const WB = { wand: 'base.rift_wand', sword: 'base.rift_blade', bow: 'base.hunter_bow' };
const builds = {
  spell: ['wand', [{ skill: 'skill.fireball', sup: [] }, { skill: null, sup: [] }, { skill: null, sup: [] }, { skill: 'skill.ice_spear', sup: [] }, { skill: null, sup: [] }, { skill: 'skill.arc_spark', sup: [] }]],
  melee: ['sword', [{ skill: 'skill.whirl_cleave', sup: [] }, { skill: null, sup: [] }, { skill: null, sup: [] }, { skill: 'skill.double_strike', sup: [] }, { skill: null, sup: [] }, { skill: 'skill.cyclone', sup: [] }]],
  ranged: ['bow', [{ skill: 'skill.split_arrow', sup: [] }, { skill: null, sup: [] }, { skill: null, sup: [] }, { skill: 'skill.power_shot', sup: [] }, { skill: null, sup: [] }, { skill: 'skill.lightning_arrow', sup: [] }]],
};
for (const [zi, lv] of [[1, 15], [2, 30], [3, 42]]) {
  const Z = Object.keys(C.ZONES)[zi];
  for (const bn in builds) {
    let dps = 0, ehp = 0;
    for (const sd of [3, 7]) {
      E.newRun(sd, Z); const g = E.game; g.godMode = true; g.noBoons = true; C.setCharacterLevel(g, lv); E.setFrozen(true);
      const [w, mains] = builds[bn]; C.setBuild(g, { mains, layout: 3 }); C.normalizeBuild(g);
      const rng = C.makeRng(sd * 31 + zi); const g2 = { rng, zoneTier: zi + 1, nextUid: 900000, riftTier: 0 };
      for (const slot of D.EQUIP_SLOTS) { const it = C.rollItem(Object.assign(g2, { player: g.player, stats: g.stats }), 'rare', slot, { ilvl: zi + 1 }); if (slot === 'weapon') { it.base = WB[w]; it.name = C.itemName(it); } g.player.equip[slot] = it; }
      C.recomputeStats(g); ehp += g.player.stats.maxHp / (1 - g.player.stats.dmgReduction) / 2;
      for (let i = 0; i < 60 * 60 && g.state === 'playing'; i++) C.step(g, C.autopilot(g), 1 / 60);
      dps += Object.values(g.stats.dmgBySource).reduce((a, b) => a + b, 0) / g.t / 2;
    }
    out['Z' + (zi + 1) + ' ' + bn] = { dps: Math.round(dps), ehp: Math.round(ehp) };
  }
}
return out;
