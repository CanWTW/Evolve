#!/usr/bin/env python3
"""EVOLVE v0.18.0 part D: gear comparison shows each auto skill's damage per second (hit × casts per second × crit)
instead of damage per hit. Usage: patch_p180d.py in.html out.html"""
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = json.load(open(src + '.en.json'))
def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:100]))
    h = h.replace(old, new)
rep("function skillDamage(g, sk) {",
    "function skillDps(g, sk) {   // v0.18 gear comparison: hit × auto casts per second (weapon speed for attacks) × crit; supports / evolution not included\n"
    "  if (!sk || sk.kind === 'buff') return 0; const s = g.player.stats, per = skillDamage(g, sk); if (!per) return 0;\n"
    "  const W = sk.attack ? attackWeapon(g, sk) : null; const cd = W ? sk.speedMod / W.aps : sk.cooldown; const rate = ((s.speedMul && s.speedMul[sk.speedType]) || 1) / Math.max(0.05, cd || 1);\n"
    "  const crit = 1 + Math.max(0, Math.min(1, s.critChance || 0)) * Math.max(0, (s.critMul || 1) - 1); return per * rate * crit * (sk.hits || 1);\n}\n"
    "function skillDamage(g, sk) {")
rep("estimateSkill,", "estimateSkill, skillDps,", 1)
rep("function autoHitLines(eq, ns) {   // v0.17: each auto skill's damage per hit with the current gear vs. the compared gear",
    "function autoHitLines(eq, ns) {   // v0.18: each auto skill's damage per SECOND with the current gear vs. the compared gear")
rep("const a = C.skillDamage(fa, sk), b = C.skillDamage(fb, sk);\n    if (Math.abs(a - b) > 0.05) out.push([sk.name + tr(' 每下'), a, b]); } return out;",
    "const a = C.skillDps(fa, sk), b = C.skillDps(fb, sk);\n    if (Math.abs(a - b) > 0.05) out.push([sk.name + tr(' 秒傷'), a, b]); } return out;")
rep("(better ? '▲' : '▼') + nm + ' ' + a.toFixed(1) + '→' + b.toFixed(1) + '  ')); }   // v0.17",
    "(better ? '▲' : '▼') + nm + ' ' + Math.round(a) + '→' + Math.round(b) + (a > 0 ? '（' + (b >= a ? '+' : '') + Math.round((b / a - 1) * 100) + '%）' : '') + '  ')); }   // v0.18 DPS")
rep("  // main skill damage per hit\n", "  // v0.18: main skill damage per second\n")
rep("const da = C.skillDamage(fa, sk), db = C.skillDamage(fb, sk); if (Math.abs(da - db) > 1e-6) out.push([sk.name + tr(' 每下'), da.toFixed(1) + ' → ' + db.toFixed(1), db > da]); }",
    "const da = C.skillDps(fa, sk), db = C.skillDps(fb, sk); if (Math.abs(da - db) > 1e-6) out.push([sk.name + tr(' 秒傷'), Math.round(da) + ' → ' + Math.round(db), db > da]); }")
EN[' 秒傷'] = ' DPS'
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok D dps', len(h))
