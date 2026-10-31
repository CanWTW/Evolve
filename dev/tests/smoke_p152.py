"""smoke_p152: stash 500, orb stacking in stash, stash bulk sell / dupes / spare orbs / sort / single sell, gear 賣晒稀有, loot filter 3."""
import sys, subprocess, time
from playwright.sync_api import sync_playwright

root, port = sys.argv[1], 8766
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ok = fail = 0
def check(name, cond, info=''):
    global ok, fail
    if cond: ok += 1; print('PASS', name)
    else: fail += 1; print('FAIL', name, info)

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        for lang in ['zh', 'en']:
            pg = b.new_page(viewport={'width': 1280, 'height': 720})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
            pg.goto('http://localhost:%d/index.html%s' % (port, '?lang=en' if lang == 'en' else ''))
            pg.wait_for_timeout(1200)
            if lang == 'en':
                pg.evaluate("() => { try { localStorage.setItem('evolve.lang','en'); } catch(e){} }")
            pg.evaluate("() => window.__evolve.startNewCharacter()")
            pg.wait_for_timeout(300)
            info = pg.evaluate("() => ({ v: document.title, cap: window.__evolve.core.DATA.STASH_CAP, scr: window.__evolve.screen })")
            check(lang + ' version + stash 500', '0.1' in info['v'] and info['cap'] >= 500, info)
            # fill the bag: 20 common, 15 magic, 15 rare, 20 legendaries (dupes likely) + orbs
            r = pg.evaluate("""() => { const E = window.__evolve, C = E.core, g = E.game, P = g.player;
              P.inventory = []; const roll = (r, n) => { for (let i = 0; i < n; i++) P.inventory.push(C.rollItem(g, r)); };
              roll('common', 20); roll('magic', 15); roll('rare', 15); roll('legendary', 20);
              const ids = P.inventory.filter((x) => x.unique).map((x) => x.unique);
              const gid = P.gems.bag[0].id; for (let i = 0; i < 6; i++) P.gems.bag.push({ uid: C.newUid(g, 'g'), id: gid, level: 1 + (i % 2) });
              E.openStash(); return { n: P.inventory.length, dupes: ids.length - new Set(ids).size, gold: Math.floor(C.availableGold(g)), scr: E.screen }; }""")
            check(lang + ' stash opens with tools', r['scr'] == 'stash' and pg.locator('#stOp_rare').count() == 1 and pg.locator('#stSort').count() == 1, r)
            # move 30 bag items into the stash by double tap
            for _ in range(30):
                c = pg.locator('#stBag .cell').first
                c.click(); c.click()
            st = pg.evaluate("() => { const s = window.__evolve.stashSave(); return { bag: s.character.inventory.items.length, st: s.stash.items.length, cap: document.getElementById('stStCap').textContent }; }")
            check(lang + ' moved 30 to stash', st['st'] == 30 and st['bag'] == 40 and ('/500' in st['cap'] or '/1000' in st['cap']), st)
            gold0 = pg.evaluate("() => Math.floor(window.__evolve.core.availableGold(window.__evolve.game))")
            # sell all commons (bag + stash), two taps
            pg.click('#stOp_common'); armed = pg.locator('#stOp_common').inner_text()
            pg.click('#stOp_common')
            s = pg.evaluate("""() => { const s = window.__evolve.stashSave(); const all = s.character.inventory.items.concat(s.stash.items);
               return { commons: all.filter((x) => x.rarity === 'common' && !x.unique).length, total: all.length, gold: Math.floor(window.__evolve.core.availableGold(window.__evolve.game)), msg: document.getElementById('stMsg').textContent }; }""")
            check(lang + ' sell commons (two tap)', s['commons'] == 0 and s['total'] == 50 and s['gold'] > gold0 and ('?' in armed or '？' in armed), (armed, s, gold0))
            # single tap then wait → disarms nothing sold
            pg.click('#stOp_rare')
            s2 = pg.evaluate("() => { const s = window.__evolve.stashSave(); return s.character.inventory.items.concat(s.stash.items).filter((x) => x.rarity === 'rare' && !x.unique).length; }")
            check(lang + ' first tap only arms', s2 == 15, s2)
            pg.click('#stOp_rare')
            s3 = pg.evaluate("() => { const s = window.__evolve.stashSave(); return s.character.inventory.items.concat(s.stash.items).filter((x) => x.rarity === 'rare' && !x.unique).length; }")
            check(lang + ' sell rares', s3 == 0, s3)
            # duplicate legendaries: one of each unique kept (best ilvl)
            pg.click('#stOp_dupes'); pg.click('#stOp_dupes')
            d = pg.evaluate("""() => { const s = window.__evolve.stashSave(); const u = s.character.inventory.items.concat(s.stash.items).filter((x) => x.unique).map((x) => x.unique); return { n: u.length, distinct: new Set(u).size }; }""")
            check(lang + ' sell duplicate legendaries', d['n'] == d['distinct'] and d['n'] > 0, d)
            # sort
            pg.click('#stSort')
            so = pg.evaluate("() => document.getElementById('stMsg').textContent")
            check(lang + ' sort', len(so) > 0, so)
            # single sell from the stash
            n0 = pg.evaluate("() => window.__evolve.stashSave().stash.items.length")
            if n0:
                pg.locator('#stSt .cell').first.click(); pg.click('#stSell')
                n1 = pg.evaluate("() => window.__evolve.stashSave().stash.items.length")
                check(lang + ' single sell', n1 == n0 - 1, (n0, n1))
            # orbs tab: stack moves, count in cells, spare orbs sold
            pg.click('#stTabG')
            for _ in range(2):
                c = pg.locator('#stBag .cell').last
                c.click(); pg.click('#stMoveAll') if pg.locator('#stMoveAll').count() else c.click()
            gs = pg.evaluate("() => { const s = window.__evolve.stashSave(); return { st: s.stash.gems.length, cap: document.getElementById('stStCap').textContent }; }")
            check(lang + ' orbs into stash, cells shown', gs['st'] >= 1 and ('/500' in gs['cap'] or '/4000' in gs['cap']), gs)
            pg.click('#stOp_orbs'); pg.click('#stOp_orbs')
            sp = pg.evaluate("""() => { const E = window.__evolve, C = E.core, s = E.stashSave(); const all = s.character.gems.list.concat(s.stash.gems).filter((x) => !C.findSocket(E.game, x.uid)); const by = {}; for (const x of all) by[x.id] = (by[x.id] || 0) + 1; return Math.max(0, ...Object.values(by)); }""")
            check(lang + ' spare orbs sold (1 unsocketed per orb)', sp <= 1, sp)
            # gear screen: 賣晒稀有 two tap
            pg.evaluate("""() => { const E = window.__evolve, C = E.core, g = E.game; for (let i = 0; i < 4; i++) g.player.inventory.push(C.rollItem(g, 'rare')); E.show('town'); E.openGear(); }""")
            pg.wait_for_timeout(100)
            pg.click('#gSellR'); r1 = pg.evaluate("() => window.__evolve.game.player.inventory.filter((x) => x.rarity === 'rare' && !x.unique).length")
            pg.click('#gSellR'); r2 = pg.evaluate("() => window.__evolve.game.player.inventory.filter((x) => x.rarity === 'rare' && !x.unique).length")
            check(lang + ' gear 賣晒稀有 two tap', r1 == 4 and r2 == 0, (r1, r2))
            # persisted: reload keeps the result
            pg.evaluate("() => window.__evolve.closeGear && window.__evolve.closeGear()")
            # loot filter 3 in a run: rare on the ground is sold on touch
            pg.evaluate("() => { window.__evolve.openOptions(); }")
            has3 = pg.locator('#optLoot option[value="3"]').count()
            pg.select_option('#optLoot', '3')
            lf = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.newRun(7, 'zone.rift_outskirts'); const g = E.game; E.setFrozen(true); E.step(1);
               const P = g.player; for (const s in P.equip) if (!P.equip[s]) { const it = C.rollItem(g, 'common', s); if (it) C.giveItem(g, it); }
               const it = C.rollItem(g, 'rare'); const n0 = P.inventory.length; C.dropItem(g, P.x + 3, P.y, it); const g0 = P.goldGained || 0;
               for (let i = 0; i < 90; i++) C.step(g, {}, 1 / 60);
               return { lf: g.lootFilter, inv: P.inventory.length - n0, gold: (P.goldGained || 0) - g0, sold: g.stats.autoSold || 0 }; }""")
            check(lang + ' loot filter 3 sells rares', has3 == 1 and lf['lf'] == 3 and lf['inv'] == 0 and lf['sold'] >= 1, lf)
            real = [e for e in errs if 'supabase' not in e.lower()]
            check(lang + ' no console errors', not real, real[:3])
            pg.close()
        b.close()
finally:
    srv.kill()
print('%d/%d' % (ok, ok + fail))
sys.exit(1 if fail else 0)
