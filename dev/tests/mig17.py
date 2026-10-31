import sys, subprocess, time, shutil, os, json
from playwright.sync_api import sync_playwright
old, new, d = sys.argv[1], sys.argv[2], sys.argv[3]
shutil.rmtree(d, ignore_errors=True); shutil.copytree(old, d)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8814', '-d', d], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = b.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/version.json*', lambda r: r.fulfill(status=404))
    pg.goto('http://localhost:8814/index.html'); pg.wait_for_timeout(1000)
    before = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.startNewCharacter(); const g = E.game;
      for (let i = 0; i < 12; i++) g.player.inventory.push(C.rollItem(g, 'rare', null, { ilvl: 1 + (i % 4) }));
      E.show('town'); E.openStash(); E.stRun('dupes'); const s = E.save; return { schema: s.schemaVersion, n: s.character.inventory.items.length, aff: s.character.inventory.items.slice(0, 4).map((it) => [it.ilvl, it.affixes.map((a) => a.id + '=' + a.value).join(' ')]) }; }""")
    shutil.copy(os.path.join(new, 'index.html'), os.path.join(d, 'index.html'))
    pg.reload(); pg.wait_for_timeout(1200)
    after = pg.evaluate("""() => { const E = window.__evolve; E.loadCurrent(); const s = E.save; return { title: document.title, schema: s && s.schemaVersion, n: s && s.character.inventory.items.length, aff: s && s.character.inventory.items.slice(0, 4).map((it) => [it.ilvl, it.affixes.map((a) => a.id + '=' + a.value).join(' ')]), log: s && (s.migrationLog || []).slice(-2) }; }""")
    print(json.dumps(before, ensure_ascii=False)); print(json.dumps(after, ensure_ascii=False)); print('errs', errs[:3])
    b.close()
finally: srv.kill()
