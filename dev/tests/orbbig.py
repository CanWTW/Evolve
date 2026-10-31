import sys, subprocess, time, json
from playwright.sync_api import sync_playwright
root, out = sys.argv[1], sys.argv[2]
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8827', '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    for (w, hh, touch, dpr) in [(1000, 462, True, 2), (1180, 820, True, 2), (740, 360, True, 3), (1366, 768, False, 1)]:
      ctx = b.new_context(viewport={'width': w, 'height': hh}, has_touch=touch, is_mobile=touch, device_scale_factor=dpr); pg = ctx.new_page()
      pg.route('**/version.json*', lambda r: r.fulfill(status=404))
      pg.goto('http://localhost:8827/index.html'); pg.wait_for_timeout(900)
      pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA; E.startNewCharacter(); const g = E.game; C.setCharacterLevel(g, 50); C.fitBuild(g);
        const ids = [].concat(...Object.values(C.GEM_IDS)); for (let i = 0; i < 146; i++) C.giveGem(g, ids[(i * 7) % ids.length], { silent: true, noAuto: i > 12 }); E.openOrbs(); }""")
      pg.wait_for_timeout(250)
      r = pg.evaluate("() => { const f = document.getElementById('oFilt').getBoundingClientRect(), b = document.getElementById('oBag').getBoundingClientRect(); return { filtH: Math.round(f.height), bagTop: Math.round(b.top), bagH: Math.round(b.height), vh: innerHeight }; }")
      print(w, hh, json.dumps(r)); pg.screenshot(path=f'{out}/v174_{w}.png'); ctx.close()
    b.close()
finally: srv.kill()
