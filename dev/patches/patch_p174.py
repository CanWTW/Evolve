#!/usr/bin/env python3
"""v0.17.3 -> v0.17.4: orb filter chips in one compact, side-scrolling row (they pushed the bag off screen)."""
import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count: raise SystemExit('expected %d got %d: %r' % (count, n, old[:80]))
    h = h.replace(old, new)
rep("#orbs.narrow .ofilt{max-width:calc(var(--obc,4)*54px)}", "")
rep(".ofilt{display:flex;gap:4px;flex-wrap:wrap;flex:0 0 auto;margin:0 0 6px}",
    ".ofilt{display:flex;gap:4px;flex-wrap:nowrap;flex:0 0 auto;margin:0 0 6px;overflow-x:auto;overflow-y:hidden;overscroll-behavior:contain;scrollbar-width:thin;touch-action:pan-x;padding-bottom:2px;min-width:0;max-width:100%}   /* v0.17.4 one row */")
rep("#ui .ofilt button{min-height:36px;min-width:44px;padding:0 10px;font-size:max(12px,calc(var(--u)*5));",
    "#ui .ofilt button{flex:0 0 auto;white-space:nowrap;min-height:32px;min-width:0;padding:0 9px;font-size:13px;")
# mouse wheel scrolls the chip row sideways
rep("function orbFiltOk(x, f) {",
    "document.addEventListener('wheel', (e) => { const f = e.target && e.target.closest && e.target.closest('.ofilt'); if (f && Math.abs(e.deltaY) > Math.abs(e.deltaX) && f.scrollWidth > f.clientWidth) { f.scrollLeft += e.deltaY; e.preventDefault(); } }, { passive: false });   // v0.17.4\n"
    "function orbFiltOk(x, f) {")
# keep the selected chip in view after re-render
rep("  const I = $('oBag'); const ist = I.scrollTop; I.textContent = '';",
    "  { const on = F.querySelector('button.on'); if (on && F.scrollWidth > F.clientWidth) { const l = on.offsetLeft - F.offsetLeft; if (l < F.scrollLeft || l + on.offsetWidth > F.scrollLeft + F.clientWidth) F.scrollLeft = Math.max(0, l - 20); } }   // v0.17.4\n"
    "  const I = $('oBag'); const ist = I.scrollTop; I.textContent = '';")
rep("#orbs .obaghd{display:flex;align-items:center;gap:8px;flex:0 0 auto;margin:0 0 6px}", "#orbs .obaghd{display:flex;align-items:center;gap:6px 8px;flex:0 0 auto;margin:0 0 6px;flex-wrap:wrap;min-width:0;max-width:100%}#orbs .obaghd .gcap{white-space:normal;min-width:0}")
rep(".rtab .rc{color:#ffd23f;white-space:nowrap}.rtab .rd{color:#9fb3c8}", ".rtab .rc{color:#ffd23f;white-space:nowrap}.rtab .rd{color:#9fb3c8}\n#oDetail .rtab{grid-template-columns:auto minmax(0,1fr)}#oDetail .rtab .rc{white-space:normal}#oDetail .rtab .rd{grid-column:1/-1;margin:-2px 0 6px}   /* v0.17.4: reactions table fits the narrow detail column */")
rep("<title>PROJECT: EVOLVE — 原型 0.17.3</title>", "<title>PROJECT: EVOLVE — 原型 0.17.4</title>")
rep("瀏覽器測試版 0.17.3 — 持續更新中", "瀏覽器測試版 0.17.4 — 持續更新中", 4)
rep("Browser beta 0.17.3", "Browser beta 0.17.4", 3)
rep("const VERSION = '0.17.3';", "const VERSION = '0.17.4';")
open(dst, 'w', encoding='utf-8').write(h); print('ok')
