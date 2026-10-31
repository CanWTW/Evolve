import sys, subprocess, time, json
from playwright.sync_api import sync_playwright
root, out, tag = sys.argv[1], sys.argv[2], sys.argv[3]
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8826', '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    for (w, hh, touch) in [(1920, 1080, False), (1366, 768, False), (915, 412, True), (740, 360, True), (667, 375, True), (390, 844, True), (1024, 1366, True)]:
      ctx = b.new_context(viewport={'width': w, 'height': hh}, has_touch=touch, is_mobile=touch); pg = ctx.new_page()
      pg.route('**/version.json*', lambda r: r.fulfill(status=404))
      pg.goto('http://localhost:8826/index.html'); pg.wait_for_timeout(900)
      pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.startNewCharacter(); const g = E.game; C.setCharacterLevel(g, 20); C.fitBuild(g);
        for (const id of ['skill.fireball','skill.ice_spear','support.multi_cast','trigger.on_kill','skill.anger']) C.giveGem(g, id, { silent: true }); E.openOrbs(); }""")
      pg.wait_for_timeout(250)
      r = pg.evaluate("() => { const q = (id) => { const e = document.getElementById(id); if (!e) return null; const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return [Math.round(r.x), Math.round(r.width), Math.round(r.height), cs.display, cs.visibility]; }; return { cls: document.getElementById('orbs').className, bar: q('oBarCol'), bag: q('oBagCol'), det: q('oDetail') }; }")
      print(w, hh, json.dumps(r))
      pg.screenshot(path=f'{out}/{tag}_o_{w}x{hh}.png'); ctx.close()
    b.close()
finally: srv.kill()
