#!/usr/bin/env python3
"""v0.17.2 -> v0.17.3: orb screen narrow layout (the bag squeezed the skill bar to 0 width on phones)."""
import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d got %d: %r' % (count, n, old[:80]))
    h = h.replace(old, new)
rep("#orbs.narrow #oBarCol{flex:1 1 auto;max-width:none}#orbs.narrow #oBagCol{flex:0 0 auto;min-width:0}",
    "#orbs.narrow #oBarCol{flex:1 1 auto;max-width:none;min-width:min(330px,58vw)}#orbs.narrow #oBagCol{flex:0 0 auto;min-width:0;max-width:40vw}\n"
    "#orbs.narrow .obag{grid-template-columns:repeat(var(--obc,4),48px)!important}#orbs.narrow .ofilt{max-width:calc(var(--obc,4)*54px)}   /* v0.17.3 */\n"
    "@media (max-width:520px){#orbs.narrow{--obc:2}#orbs.narrow #oBarCol{min-width:0}}")
rep("<title>PROJECT: EVOLVE — 原型 0.17.2</title>", "<title>PROJECT: EVOLVE — 原型 0.17.3</title>")
rep("瀏覽器測試版 0.17.2 — 持續更新中", "瀏覽器測試版 0.17.3 — 持續更新中", 4)
rep("Browser beta 0.17.2", "Browser beta 0.17.3", 3)
rep("const VERSION = '0.17.2';", "const VERSION = '0.17.3';")
open(dst, 'w', encoding='utf-8').write(h); print('ok')
