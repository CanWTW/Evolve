#!/usr/bin/env python3
"""EVOLVE v0.16.0 part E: balance pass from the Z3 / Lv30 autopilot sims (spells + minions: base damage; attacks: attack speed,
so the % numbers in the descriptions stay true). Usage: patch_p160d.py in.html out.html"""
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = json.load(open(src + '.en.json'))

# skill → damage-per-second multiplier (spells / minions scale baseDamage, attacks scale attack speed)
BAL = {'contagion': 0.35, 'summon_spiders': 0.44, 'caustic_arrow': 0.48, 'meteor': 0.6, 'frost_mine': 0.637, 'flame_field': 0.8, 'blade_vortex': 0.95, 'explosive_arrow': 0.68, 'rain_arrows': 0.68, 'poison_pool': 0.637, 'cluster_darts': 0.85, 'venom_slash': 1.1, 'cyclone': 1.0, 'frost_nova': 3.6, 'storm_turret': 2.47, 'quick_shot': 2.16, 'dart_fan': 2.04, 'ice_shards': 1.6, 'heavy_strike': 1.7, 'infernal_blow': 1.6, 'split_arrow': 1.68, 'deadeye_shot': 1.4, 'tornado_shot': 1.4, 'power_shot': 1.3, 'lightning_arrow': 1.3, 'arc_spark': 1.3, 'ice_spear': 1.35, 'frost_rounds': 1.69, 'frost_wolf': 1.5, 'flame_spirits': 1.3, 'double_strike': 1.3, 'scattershot': 1.2, 'ricochet_blades': 1.15}
js = "\n// v0.16 balance pass (Z3 Lv30 autopilot sims): spells / minions → base damage, attacks → attack speed (so the % in descriptions stay true)\n"
js += "for (const [id, m] of " + json.dumps([['skill.' + k, v] for k, v in BAL.items()]) + ") { const sk = SKILLS[id]; if (!sk) continue; if (sk.attack) sk.speedMod = +(sk.speedMod / m).toFixed(3); else sk.baseDamage = +(sk.baseDamage * m).toFixed(2); }\n"
js += "SKILLS['skill.frost_nova'].castRange = 110;   // v0.16: it almost never fired while kiting\n"
anchor = "const GEM_IDS = { active: Object.keys(SKILLS),"
assert h.count(anchor) == 1
h = h.replace(anchor, js + anchor)
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok balance')
# three auto skills deal ~1.4-1.7x what one ★primary did → zones 2-4 get tougher (Z1 stays as is: only one auto slot until Lv6)
h = open(dst, encoding='utf-8').read()
for old, new in [("recLevel: 12, hpMul: 2.6,", "recLevel: 12, hpMul: 3.25,"), ("recLevel: 26, hpMul: 6.5,", "recLevel: 26, hpMul: 8.45,"), ("recLevel: 40, hpMul: 13,", "recLevel: 40, hpMul: 16.9,")]:
    assert h.count(old) == 1, old; h = h.replace(old, new)
open(dst, 'w', encoding='utf-8').write(h)
print('ok zone hp')
