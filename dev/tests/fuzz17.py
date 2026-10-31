import sys, subprocess, time, shutil, os, json
from playwright.sync_api import sync_playwright
old, new, d = sys.argv[1], sys.argv[2], sys.argv[3]
shutil.rmtree(d, ignore_errors=True); shutil.copytree(old, d)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8816', '-d', d], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = b.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/version.json*', lambda r: r.fulfill(status=404))
    pg.goto('http://localhost:8816/index.html'); pg.wait_for_timeout(1000)
    # play-like: a character with many items of every rarity / tier, rift-tier legendaries (ilvl 5/6), stash, gems
    pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.startNewCharacter(); const g = E.game; C.setCharacterLevel(g, 45);
      g.riftTier = 15; for (let i = 0; i < 400; i++) { const r = ['common','magic','rare','legendary'][i % 4]; g.player.inventory.push(C.rollItem(g, r, null, r === 'legendary' ? {} : { ilvl: 1 + (i % 6) })); }
      E.show('town'); E.openStash();
      const s = E.stashSave(); }""")
    res = pg.evaluate("""() => { const E = window.__evolve, C = E.core; const g = E.game;
      // move most to the stash through the real code path
      E.commitVillage ? 0 : 0; const s0 = E.save; return { n: s0.character.inventory.items.length, schema: s0.schemaVersion }; }""")
    # save through village commit (bag limited to 80 → overflow handled by game), then also write directly
    st = pg.evaluate("""() => { const E = window.__evolve, C = E.core; const s = JSON.parse(JSON.stringify(E.save)); const g = E.game;
      s.character.inventory.items = g.player.inventory.slice(0, 80).map(C.Save.toSaveItem); s.stash = s.stash || { capacity: 200, items: [], gems: [] };
      s.stash.items = g.player.inventory.slice(80, 280).map(C.Save.toSaveItem); s.character.level = 45;
      const r = E.saves.save(0, s); return { ok: r.ok, err: r.errors || r.error }; }""")
    print('old write', st)
    print('raw before', pg.evaluate("() => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith('evolve.save')) { const v = localStorage.getItem(k); let n = null; try { const d = JSON.parse(v); n = d.character ? [d.schemaVersion, d.character.inventory.items.length, d.stash && d.stash.items.length] : null; } catch (e) {} o[k] = [v.length, n]; } } return o; }"))
    shutil.copy(os.path.join(new, 'index.html'), os.path.join(d, 'index.html'))
    pg.reload(); pg.wait_for_timeout(1200)
    r = pg.evaluate("""() => { const E = window.__evolve; const r = E.saves.load(0); return { ok: r.ok, reason: r.reason, errors: (r.errors || []).slice(0, 5), error: r.error, schema: r.data && r.data.schemaVersion, n: r.data && r.data.character.inventory.items.length }; }""")
    print('raw after', pg.evaluate("() => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith('evolve.save')) { const v = localStorage.getItem(k); let n = null; try { const d = JSON.parse(v); n = d.character ? [d.schemaVersion, d.character.inventory.items.length, d.stash && d.stash.items.length, (d.migrationLog||[]).slice(-3).map(x=>x.kind)] : null; } catch (e) {} o[k] = [v.length, n]; } } return o; }"))
    print('why', pg.evaluate("() => { const E = window.__evolve, C = E.core; const d = JSON.parse(localStorage.getItem('evolve.save.v1.slot0.corrupt')); try { const m = C.Save.migrateSave(d, 5); return C.Save.validateSave(m).slice(0, 6); } catch (e) { return 'throw ' + e.message; } }"))
    print('new load', json.dumps(r, ensure_ascii=False)); print('errs', errs[:3])
    b.close()
finally: srv.kill()
