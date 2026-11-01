"""smoke_p181: ground fx (fissures, rocks, dust, wind), legendary / set affix counts, old items topped up on load."""
import sys, subprocess, time, json
from playwright.sync_api import sync_playwright
root, shots = sys.argv[1], sys.argv[2]; port = 8821
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
ok = fail = 0
def check(n, c, i=''):
    global ok, fail
    if c: ok += 1; print('PASS', n)
    else: fail += 1; print('FAIL', n, json.dumps(i, ensure_ascii=False)[:500])
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/version.json*', lambda r: r.fulfill(status=404))
        pg.goto('http://localhost:%d/index.html' % port); pg.wait_for_timeout(900)
        check('version 0.18.1', '0.18.1' in pg.title(), pg.title())
        pg.evaluate("() => window.__evolve.startNewCharacter()")
        A = pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA, g = E.game; const out = { set: [], uq: [] };
          for (let i = 0; i < 20; i++) { const it = C.rollItem(g, 'legendary', null, { ilvl: 3 }); const u = D.UNIQUES[it.unique]; (u.set ? out.set : out.uq).push(it.affixes.length); }
          const r = C.rollItem(g, 'rare', 'body', { ilvl: 3 }); out.rare = r.affixes.length; return out; }""")
        check('set pieces roll 3 random affixes', A['set'] and all(n == 3 for n in A['set']), A)
        check('other legendaries roll 2', A['uq'] and all(n == 2 for n in A['uq']), A)
        # an old set piece with 1 affix is topped up to 3 on load
        T = pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA; E.loadCurrent(); E.enterVillage(); const g = E.game;
          const u = Object.values(D.UNIQUES).find((x) => x.set); const it = C.rollItem(g, 'legendary', u.slot, { set: u.set, ilvl: 3 }); it.unique = u.id; it.base = u.base; it.affixes = it.affixes.slice(0, 1); it.name = C.itemName(it);
          g.player.inventory.push(it); E.commitVillage(); return it.uid; }""")
        pg.reload(); pg.wait_for_timeout(900)
        L = pg.evaluate("(uid) => { const E = window.__evolve; E.loadCurrent(); const it = E.save.character.inventory.items.find((x) => x.uid === uid); return { n: it && it.affixes.length, log: (E.save.migrationLog || []).map((l) => l.kind) }; }", T)
        check('old set piece topped up to 3 affixes on load', L['n'] == 3 and 'legendary-affixes-added' in L['log'], L)
        # ground fx spawn
        G = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.newRun(5, 'zone.ember_canyon'); const g = E.game; E.setFrozen(true); g.noSpawns = true; g.godMode = true; C.setCharacterLevel(g, 30);
          const it = C.rollItem(g, 'rare', 'weapon', { ilvl: 4 }); it.base = 'base.iron_axe'; it.name = C.itemName(it); g.player.equip.weapon = it;
          C.setBuild(g, { mains: [{ skill: 'skill.earthquake', sup: [] }], layout: 3 }); C.normalizeBuild(g); C.recomputeStats(g); g.enemies.length = 0;
          for (let i = 0; i < 4; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 30 + i * 10, g.player.y, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
          for (let k = 0; k < 75; k++) { C.step(g, {}, 1 / 60); E.render(); }
          const F = E.gfx; return { scars: F.scars.length, fis: F.scars.filter((s) => s.kind === 'fissure').length, rocks: F.rocks.length, dust: F.dust.length }; }""")
        check('earthquake leaves fissures, rocks and dust', G['fis'] >= 2 and G['rocks'] > 0 and G['dust'] > 0, G)
        W = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.newRun(6, 'zone.ember_canyon'); const g = E.game; E.setFrozen(true); g.noSpawns = true; g.godMode = true; C.setCharacterLevel(g, 30);
          const it = C.rollItem(g, 'rare', 'weapon', { ilvl: 4 }); it.base = 'base.rift_blade'; it.name = C.itemName(it); g.player.equip.weapon = it;
          C.setBuild(g, { mains: [{ skill: 'skill.cyclone', sup: [] }], layout: 3 }); C.normalizeBuild(g); C.recomputeStats(g); g.enemies.length = 0;
          for (let i = 0; i < 4; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 20 + i * 8, g.player.y, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
          for (let k = 0; k < 40; k++) { C.step(g, {}, 1 / 60); E.render(); } return !!(g._vortex && g._vortex.until > g.t); }""")
        check('cyclone keeps a whirlwind around the player', W, W)
        R = pg.evaluate("() => { const E = window.__evolve; E.opts && (E.opts.reduceFx = true); return 1; }")
        real = [e for e in errs]
        check('no page errors', not real, real[:3])
        b.close()
finally:
    srv.kill()
print('%d/%d' % (ok, ok + fail)); sys.exit(1 if fail else 0)
