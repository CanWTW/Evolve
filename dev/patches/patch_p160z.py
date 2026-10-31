#!/usr/bin/env python3
"""final step: EN strings collected by earlier parts + version 0.16.0. Usage: patch_p160z.py in.html out.html"""
import sys, json, os
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read(); EN = json.load(open(src + '.en.json'))
def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d got %d: %r' % (count, n, old[:80]))
    h = h.replace(old, new)
rep("<title>PROJECT: EVOLVE — 原型 0.15.2</title>", "<title>PROJECT: EVOLVE — 原型 0.16.0</title>")
rep("瀏覽器原型 0.15.2（M0 + M1）", "瀏覽器原型 0.16.0（M0 + M1）", 2)
rep("const VERSION = '0.15.2';", "const VERSION = '0.16.0';")
rep("Browser prototype 0.15.1 (M0 + M1)", "Browser prototype 0.16.0 (M0 + M1)")
rep("const norm = (t) => t.replace(/\\s+/g, ' ').trim();", "Object.assign(EN, " + json.dumps(EN, ensure_ascii=False) + ");   // v0.16\nconst norm = (t) => t.replace(/\\s+/g, ' ').trim();")
open(dst, 'w', encoding='utf-8').write(h); print('ok final', len(EN), 'strings')
