import sys, subprocess, time, shutil, os, json
from playwright.sync_api import sync_playwright
s161, s170, s171, d = sys.argv[1:5]
shutil.rmtree(d, ignore_errors=True); shutil.copytree(s161, d)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8819', '-d', d], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
ok = fail = 0
def check(n, c, i=''):
    global ok, fail
    if c: ok += 1; print('PASS', n)
    else: fail += 1; print('FAIL', n, json.dumps(i, ensure_ascii=False)[:500])
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = b.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/version.json*', lambda r: r.fulfill(status=404))
    pg.goto('http://localhost:8819/index.html'); pg.wait_for_timeout(1000)
    # 0.16.1: Lv45 character "Veteran" with 280 items of every tier
    pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.startNewCharacter(); const g = E.game; g.riftTier = 15; const items = [];
      for (let i = 0; i < 400; i++) { const r = ['common','magic','rare','legendary'][i % 4]; items.push(C.rollItem(g, r, null, r === 'legendary' ? {} : { ilvl: 1 + (i % 6) })); }
      const s = JSON.parse(JSON.stringify(E.save)); s.character.name = 'Veteran'; s.character.level = 45; s.character.inventory.items = items.slice(0, 80).map(C.Save.toSaveItem);
      s.stash = { capacity: 500, items: items.slice(80, 280).map(C.Save.toSaveItem), gems: [] }; return E.saves.save(0, s).ok; }""")
    # 0.17.0 loads it → rejects → old backup; player makes a new character in the same slot
    shutil.copy(os.path.join(s170, 'index.html'), os.path.join(d, 'index.html')); pg.reload(); pg.wait_for_timeout(1200)
    r = pg.evaluate("() => { const E = window.__evolve; E.loadCurrent(); return { name: E.save && E.save.character.name, n: E.save && E.save.character.inventory.items.length }; }")
    check('0.17.0 lost it (reproduced)', r['n'] == 0, r)
    pg.evaluate("() => { const E = window.__evolve; E.saves.createCharacter(0, { name: 'Fresh', overwrite: true }); E.loadCurrent(); }")
    # 0.17.1
    shutil.copy(os.path.join(s171, 'index.html'), os.path.join(d, 'index.html')); pg.reload(); pg.wait_for_timeout(1200)
    warn = pg.evaluate("() => document.getElementById('titleWarn').textContent")
    check('title says a character can be recovered', 'recover' in warn.lower() or '恢復' in warn, warn)
    pk = pg.evaluate("() => window.__evolve.saves.peekCorrupt(0)")
    check('peekCorrupt finds Veteran Lv45', pk and pk['name'] == 'Veteran' and pk['level'] == 45 and pk['items'] == 280, pk)
    pg.evaluate("() => document.getElementById('btnStart') && 0"); pg.evaluate("() => { const E = window.__evolve; E.openSlots ? E.openSlots() : null; }")
    has = pg.evaluate("() => { if (!document.getElementById('slotRec0')) { const f = Object.values(window.__evolve).find((v) => typeof v === 'function' && v.name === 'openSlots'); } return !!document.getElementById('slotRec0'); }")
    if not has:
        pg.evaluate("() => { const b = [...document.querySelectorAll('button')].find((x) => /Characters|角色/.test(x.textContent) && x.offsetParent); b && b.click(); }"); pg.wait_for_timeout(200)
        b2 = pg.evaluate("() => { const b = [...document.querySelectorAll('button')].find((x) => /Characters|角色/.test(x.textContent) && x.offsetParent); b && b.click(); return !!document.getElementById('slotRec0'); }"); pg.wait_for_timeout(200)
    pg.screenshot(path=sys.argv[5] + '/v171_slots.png')
    pg.click('#slotRec0'); pg.wait_for_timeout(300)
    after = pg.evaluate("() => { const E = window.__evolve, o = []; for (let i = 0; i < 3; i++) { const q = E.saves.peek(i); o.push(q && !q.corrupt ? [q.name, q.level] : null); } return { slots: o, cur: E.save && [E.save.character.name, E.save.character.inventory.items.length, E.save.stash.items.length], corrupt: E.saves.peekCorrupt(0) }; }")
    check('restored to slot 2, Fresh kept, items intact', after['slots'][0] == ['Fresh', 1] and after['slots'][1] == ['Veteran', 45] and after['cur'] == ['Veteran', 80, 200] and after['corrupt'] is None, after)
    print('errs', errs[:3]); b.close()
finally: srv.kill()
print('%d/%d' % (ok, ok + fail)); sys.exit(1 if fail else 0)
