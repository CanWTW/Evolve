#!/usr/bin/env python3
"""v0.17.1 -> v0.17.2: codex sets tab (SETS read from C, not DATA)."""
import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d got %d: %r' % (count, n, old[:80]))
    h = h.replace(old, new)
rep("const S = D.SETS[u.set];", "const S = C.SETS[u.set];")
rep("<title>PROJECT: EVOLVE — 原型 0.17.1</title>", "<title>PROJECT: EVOLVE — 原型 0.17.2</title>")
rep("瀏覽器測試版 0.17.1 — 持續更新中", "瀏覽器測試版 0.17.2 — 持續更新中", 4)
rep("Browser beta 0.17.1", "Browser beta 0.17.2", 3)
rep("const VERSION = '0.17.1';", "const VERSION = '0.17.2';")
rep('"瀏覽器測試版 0.17.2 — 持續更新中":"Browser beta 0.17.2 — updated often"', '"瀏覽器測試版 0.17.2 — 持續更新中":"Browser beta 0.17.2 — updated often"') if '"瀏覽器測試版 0.17.2 — 持續更新中":"Browser beta 0.17.2 — updated often"' in h else None
open(dst, 'w', encoding='utf-8').write(h); print('ok')
