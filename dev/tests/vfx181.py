import sys, subprocess, time
from playwright.sync_api import sync_playwright
root, out = sys.argv[1], sys.argv[2]
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8816', '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
WB = {'bow': 'base.hunter_bow', 'sword': 'base.rift_blade', 'axe': 'base.iron_axe'}
errs = []
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = b.new_page(viewport={'width': 960, 'height': 540})
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/version.json*', lambda r: r.fulfill(status=404))
    pg.goto('http://localhost:8816/index.html'); pg.wait_for_timeout(900); pg.evaluate("() => window.__evolve.startNewCharacter()")
    for sid, w, steps in [('skill.earthquake', 'axe', 24), ('skill.earthquake', 'axe', 70), ('skill.ground_slam', 'axe', 14), ('skill.leap_slam', 'axe', 30), ('skill.cyclone', 'sword', 40), ('skill.whirl_cleave', 'sword', 8), ('skill.meteor', None, 75), ('skill.frost_nova', None, 14), ('skill.tornado_shot', 'bow', 16), ('skill.heavy_strike', 'axe', 10), ('skill.fireball', None, 30)]:
      pg.evaluate("""([sid, w]) => { const E = window.__evolve, C = E.core; E.newRun(5, 'zone.ember_canyon'); const g = E.game; E.setFrozen(true); g.noSpawns = true; g.godMode = true; C.setCharacterLevel(g, 30);
        if (w) { const it = C.rollItem(g, 'rare', 'weapon', { ilvl: 4 }); it.base = w; it.name = C.itemName(it); g.player.equip.weapon = it; }
        C.setBuild(g, { mains: [{ skill: sid, sup: [] }], layout: 3 }); C.normalizeBuild(g); C.recomputeStats(g); g.enemies.length = 0;
        for (let i = 0; i < 6; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 30 + (i % 3) * 16, g.player.y - 16 + Math.floor(i / 3) * 24, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
        g.player.build.mains[0].cd = 0; return 1; }""", [sid, WB.get(w)])
      for k in range(steps): pg.evaluate("() => { const E = window.__evolve; E.core.step(E.game, {}, 1/60); E.render(); }"); pg.wait_for_timeout(8)
      pg.screenshot(path=f"{out}/v181_{sid.split('.')[1]}_{steps}.png", clip={'x': 300, 'y': 150, 'width': 360, 'height': 240})
    b.close()
finally: srv.kill()
print('errs', errs[:3])
