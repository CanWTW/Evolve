#!/usr/bin/env python3
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read(); EN = json.load(open(src + '.en.json'))
def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d got %d: %r' % (count, n, old[:80]))
    h = h.replace(old, new)
rep("<title>PROJECT: EVOLVE — 原型 0.16.1</title>", "<title>PROJECT: EVOLVE — 原型 0.17.0</title>")
rep("瀏覽器原型 0.16.1（M0 + M1）— 唔係正式遊戲", "瀏覽器測試版 0.17.0 — 持續更新中", 2)
rep("Browser prototype 0.16.1 (M0 + M1)", "Browser beta 0.17.0")
rep("const VERSION = '0.16.1';", "const VERSION = '0.17.0';")
EN['瀏覽器測試版 0.17.0 — 持續更新中'] = 'Browser beta 0.17.0 — updated often'
rep("const norm = (t) => t.replace(/\\s+/g, ' ').trim();", "Object.assign(EN, " + json.dumps(EN, ensure_ascii=False) + ");   // v0.17\nconst norm = (t) => t.replace(/\\s+/g, ' ').trim();")
open(dst, 'w', encoding='utf-8').write(h); print('ok final', len(EN))
