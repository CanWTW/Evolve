"""smoke_p170: gear scaling by item level, full comparison, save schema 4 → 5 proportional conversion, stash fusion / deposit,
codex + collection, per-skill sounds registered, layout widths. Usage: smoke_p170.py <site> <shots dir>"""
import sys, subprocess, time, json
from playwright.sync_api import sync_playwright
root, shots = sys.argv[1], sys.argv[2]; port = 8813
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
ok = fail = 0
def check(n, c, i=''):
    global ok, fail
    if c: ok += 1; print('PASS', n)
    else: fail += 1; print('FAIL', n, json.dumps(i, ensure_ascii=False)[:600])
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if (m.type == 'error' and 'Failed to load' not in m.text) or 'validation' in m.text else None)
        pg.route('**/version.json*', lambda r: r.fulfill(status=404))
        pg.goto('http://localhost:%d/index.html' % port); pg.wait_for_timeout(1000)
        check('version 0.17.x', '0.17.' in pg.title(), pg.title())
        pg.evaluate("() => window.__evolve.startNewCharacter()")
        R = pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA, g = E.game, R = {};
          const mk = (base, ilvl, rar) => { const it = C.rollItem(g, rar || 'common', D.BASES[base].type, { ilvl }); it.base = base; it.affixes = []; it.special = null; it.unique = null; it.name = C.itemName(it); return it; };
          R.sword = [1, 3, 6].map((t) => { const w = C.weaponAt(mk('base.rift_blade', t)); return [w.min, w.max]; });
          R.wand = [1, 3, 6].map((t) => (C.weaponAt(mk('base.rift_wand', t)).spellPower || 0));
          R.plate = [1, 3, 6].map((t) => C.itemMods(mk('base.iron_plate', t)).find((m) => m.stat === 'maxHpFlat').value);
          R.boots = [1, 3, 6].map((t) => C.itemMods(mk('base.dust_boots', t)).find((m) => m.stat === 'moveSpeedInc').value);
          R.range = [1, 3, 6].map((t) => C.affixRange(D.AFFIX_BY_ID['aff.hp'], t));
          const u = Object.values(D.UNIQUES).find((x) => !x.set && x.mods.some((m) => m.value > 0)); R.uq = [1, 6].map((t) => { const it = mk(u.base, t, 'legendary'); it.unique = u.id; return JSON.stringify(C.itemMods(it).filter((m) => !m.flag)); });
          R.desc3 = C.describeItem(mk('base.rift_blade', 3)).map((l) => l.text);
          return R; }""")
        check('weapon damage grows with item level', R['sword'][0][0] < R['sword'][1][0] < R['sword'][2][0], R['sword'])
        check('wand spell power 0 at tier 1, grows', R['wand'][0] == 0 and 0 < R['wand'][1] < R['wand'][2], R['wand'])
        check('implicits grow (flat + pct)', R['plate'][0] < R['plate'][1] < R['plate'][2] and R['boots'][0] < R['boots'][1] < R['boots'][2], [R['plate'], R['boots']])
        check('affix ranges steeper', R['range'][2][1] >= R['range'][0][1] * 6, R['range'])
        check('legendary lines grow at higher grade', R['uq'][0] != R['uq'][1], R['uq'])
        check('item level line in description', any('Item level 3' in l or '物品等級 3' in l for l in R['desc3']), R['desc3'])
        # comparison shows attack speed / per-skill damage lines
        C2 = pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA; E.newRun(4, 'zone.rift_outskirts'); const g = E.game; E.setFrozen(true); C.setCharacterLevel(g, 30);
          C.setBuild(g, { mains: [{ skill: 'skill.whirl_cleave', sup: [] }], layout: 3 }); C.normalizeBuild(g);
          const w1 = C.rollItem(g, 'common', 'weapon', { ilvl: 1 }); w1.base = 'base.rift_blade'; w1.affixes = []; w1.name = C.itemName(w1); g.player.equip.weapon = w1; C.recomputeStats(g);
          const w3 = C.rollItem(g, 'common', 'weapon', { ilvl: 3 }); w3.base = 'base.rift_blade'; w3.affixes = []; w3.name = C.itemName(w3); g.player.inventory = [w3];
          E.openGear(); return 1; }""")
        pg.wait_for_timeout(150); pg.evaluate("() => { const c = document.querySelector('#gInv .gcell'); c && c.click(); }"); pg.wait_for_timeout(150)
        diff = pg.evaluate("() => (document.querySelector('#gDetail .diff') || {}).textContent || ''")
        check('compare shows per-skill hit + attack speed', ('Whirl' in diff or '旋風' in diff) and ('Attack speed' in diff or '攻擊速度' in diff), diff[:300])
        pg.screenshot(path=shots + '/v17_gear.png')
        # stash fusion + deposit
        F = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.loadCurrent(); E.enterVillage && E.enterVillage(); const g = E.game;
          for (let i = 0; i < 9; i++) C.giveGem(g, 'support.area', { silent: true, noAuto: true }); g.player.goldGained = (g.player.goldGained || 0) + 5000;
          E.openStash(); document.getElementById('stTabG').click(); E.stDepositOrbs(); const s = E.stashSave();
          const lv = {}; for (const x of s.stash.gems.filter((q) => q.id === 'support.area')) lv[x.level] = (lv[x.level] || 0) + 1; return { lv, gold: s.character.gold, bag: s.character.gems.list.length }; }""")
        check('deposit + stash auto-fuse (9 Lv1 → 1 Lv3)', F['lv'] == {'3': 1}, F)
        pg.screenshot(path=shots + '/v17_stash.png')
        # codex + collection
        X = pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA, g = E.game;
          const u = Object.values(D.UNIQUES).find((x) => !x.set); const mkU = (t) => { const it = C.rollItem(g, 'legendary', u.slot, { ilvl: t }); it.unique = u.id; it.base = u.base; it.name = C.itemName(it); return it; };
          g.player.inventory.push(mkU(1), mkU(3), mkU(2)); E.show('town'); E.openCodex(); E.cxTab = 'uniq'; E.cxSel = u.id; E.renderCodex();
          const before = E.save.character.inventory.items.filter((x) => x.unique === u.id).length; E.cxCollectBest(u.id);
          const col = E.save.progress.collection[u.id]; const after = E.save.character.inventory.items.filter((x) => x.unique === u.id).length;
          const orbs = Object.keys(E.save.progress.codexOrbs || {}).length; return { id: u.id, colIlvl: col && col.ilvl, before, after, orbs, rows: document.querySelectorAll('#cxBody .cxrow').length }; }""")
        check('collect best (ilvl 3 of 1/2/3) leaves the bag', X['colIlvl'] == 3 and X['after'] == X['before'] - 1, X)
        check('codex lists legendaries + records orbs', X['rows'] >= 5 and X['orbs'] >= 2, X)
        pg.screenshot(path=shots + '/v17_codex_u.png')
        SX = pg.evaluate("() => { const E = window.__evolve; let err = null; try { E.cxTab = 'sets'; E.renderCodex(); } catch (e) { err = e.message; } return { err, rows: document.querySelectorAll('#cxBody .cxrow').length, grp: document.querySelectorAll('#cxBody .cxgrp').length }; }")
        check('codex sets tab: 4 sets, 16 pieces', SX['err'] is None and SX['rows'] == 16 and SX['grp'] == 4, SX)
        pg.evaluate("() => { const E = window.__evolve; E.cxTab = 'orbs'; E.cxSel = 'support.area'; E.renderCodex(); }"); pg.wait_for_timeout(100)
        pg.screenshot(path=shots + '/v17_codex_o.png')
        T = pg.evaluate("() => { const E = window.__evolve; E.cxTakeOut(Object.keys(E.save.progress.collection)[0]); return Object.keys(E.save.progress.collection).length; }")
        check('take out of the collection', T == 0, T)
        # schema 4 save → 5: proportional conversion
        M = pg.evaluate("""() => { const E = window.__evolve, C = E.core, D = C.DATA; const s = JSON.parse(JSON.stringify(E.save)); s.schemaVersion = 4;
          const it = { uid: 'i_9001', slot: 'body', base: 'base.iron_plate', rarity: 'rare', ilvl: 3, reqLevel: 28, affixes: [{ id: 'aff.hp', stat: 'maxHpFlat', value: 84 }, { id: 'aff.vit', stat: 'VIT', value: 10 }, { id: 'aff.dr', stat: 'dmgReduction', value: 0.16 }], special: null, unique: null };
          s.character.inventory.items.push(it); s.nextUid = Math.max(s.nextUid || 1, 9002); const m = C.Save.migrateSave(s, 5); const probs = C.Save.validateSave(m);
          const got = m.character.inventory.items.find((x) => x.uid === 'i_9001'); return { ok: !probs.length, probs, schema: m.schemaVersion, aff: got && got.affixes.map((a) => a.value) }; }""")
        check('schema 5 + proportional conversion (84 hp @Z3 max → 98, VIT 10 → 14, DR 0.16 → 0.18)', M['ok'] and M['schema'] == 5 and M['aff'] in ([98, 14, 0.18], [98, 14, 0.17]), M)
        snd = pg.evaluate("() => window.__evolve.SFX.names.filter((n) => n.startsWith('sk:')).length")
        check('per-skill sounds registered', snd >= 40, snd)
        real = [e for e in errs if 'supabase' not in e.lower()]
        check('no console errors / validation warnings', not real, real[:4])
        for (w, hh, touch) in [(1024, 768, False), (844, 390, True)]:
            ctx = b.new_context(viewport={'width': w, 'height': hh}, has_touch=touch, is_mobile=touch); q = ctx.new_page(); q.route('**/version.json*', lambda r: r.fulfill(status=404))
            q.goto('http://localhost:%d/index.html' % port); q.wait_for_timeout(900)
            L = q.evaluate("""() => { const E = window.__evolve, C = E.core; E.startNewCharacter(); const g = E.game; C.setCharacterLevel(g, 30); C.fitBuild(g);
              for (const id of ['skill.fireball', 'skill.ice_spear', 'skill.arc_spark', 'support.multi_cast', 'support.pierce', 'trigger.on_kill', 'skill.meteor']) C.giveGem(g, id, { silent: true }); E.openOrbs();
              const bar = document.getElementById('oBarCol').getBoundingClientRect(), bag = document.getElementById('oBagCol').getBoundingClientRect(); return { bar: Math.round(bar.width), bag: Math.round(bag.width), narrow: document.getElementById('orbs').classList.contains('narrow') }; }""")
            q.wait_for_timeout(150); q.screenshot(path=shots + '/v17_orbs_%d.png' % w)
            check('orb columns balanced at %d' % w, L['narrow'] or (L['bag'] >= 170 and L['bar'] <= 660), L)
            q.evaluate("() => { window.__evolve.show('town'); window.__evolve.openCodex(); }"); q.wait_for_timeout(150); q.screenshot(path=shots + '/v17_codex_%d.png' % w)
            ctx.close()
        b.close()
finally:
    srv.kill()
print('%d/%d' % (ok, ok + fail)); sys.exit(1 if fail else 0)
