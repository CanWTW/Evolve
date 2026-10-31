"""smoke_p161: movement skills travel over several frames (warp / blink hide the player), fusion awakens with a banner and bursts,
resonance pulses deal damage, evolution assists. Usage: smoke_p161.py <site>"""
import sys, subprocess, json, os
here = os.path.dirname(os.path.abspath(__file__)); site = sys.argv[1]
out = os.path.join(here, '_t161.json')
for z, lv, tag in [('zone.rift_outskirts', 20, 'z1'), ('zone.frozen_abyss', 30, 'z3')]:
    js = os.path.join(here, '_t161_%s.js' % tag)
    open(js, 'w').write("window.__Z='%s'; window.__LV=%d;\n" % (z, lv) + open(os.path.join(here, 't161z.js')).read())
    subprocess.run([sys.executable, os.path.join(here, 'ev2.py'), site, js, out + tag, '8799'], cwd=here, check=True, capture_output=True)
ok = fail = 0
def check(n, c, i=''):
    global ok, fail
    if c: ok += 1; print('PASS', n)
    else: fail += 1; print('FAIL', n, json.dumps(i, ensure_ascii=False)[:400])
d = json.load(open(out + 'z1'))
for sid in ['skill.flame_dash', 'skill.lightning_warp', 'skill.frostblink']:
    v = d[sid]; check(sid + ' travels over frames + hits', v['frames'] >= 6 and v['dx'] > 100 and v['dmg'] > 0, v)
check('warp/blink hide the player while travelling', d['skill.lightning_warp']['hidden'] > 0 and d['skill.frostblink']['hidden'] > 0 and d['skill.flame_dash']['hidden'] == 0, d)
check('flame dash lays ground while moving', d['skill.flame_dash']['zonesMid'] >= 3, d['skill.flame_dash'])
check('streak / ice statue fx', 'streak' in d['skill.lightning_warp']['fx'] and 'icestatue' in d['skill.frostblink']['fx'], d)
for tag in ['z1', 'z3']:
    f = json.load(open(out + tag))['fusion']
    check(tag + ' fusion awakens with banner and bursts', f['fusAt'] is not None and f['casts'] >= 2 and any('✦' in b for b in f['banners']), f)
    check(tag + ' evolution banners', sum(1 for b in f['banners'] if 'II' in b or ' I ' in b or 'I ·' in b) >= 3, f['banners'])
    check(tag + ' resonance pulses deal damage', f['pulses'] >= 5 and f['resoDmg'] > 0, f)
    lo = 0.08 if tag == 'z3' else 0.03; check(tag + ' fusion share of damage', lo <= f['dmg'] / max(1, f['total']) <= 0.6, [f['dmg'], f['total']])
print('%d/%d' % (ok, ok + fail)); sys.exit(1 if fail else 0)
