"""smoke_p160: v0.16 skill bar (3 auto slots), socket rules, link source picker, save migration, scorched, new skills,
evolution / fusion / resonance, orb screen + codex UI. Usage: smoke_p160.py <site> <shots dir>"""
import sys, subprocess, time, json
from playwright.sync_api import sync_playwright

root, shots = sys.argv[1], sys.argv[2]; port = 8795
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.8)
ok = fail = 0
def check(name, cond, info=''):
    global ok, fail
    if cond: ok += 1; print('PASS', name)
    else: fail += 1; print('FAIL', name, json.dumps(info, ensure_ascii=False)[:600])

CORE = r"""() => {
  const E = window.__evolve, C = E.core, D = C.DATA, R = {};
  const fresh = (lv) => { E.newRun(5, 'zone.rift_outskirts'); const g = E.game; E.setFrozen(true); g.noSpawns = true; g.godMode = true; C.setCharacterLevel(g, lv); C.fitBuild(g); return g; };
  // slots
  R.shape = [1, 6, 8, 14, 18].map((l) => C.slotShape(l).mains); R.roles = [0, 1, 2, 3, 4, 5, 6].map(C.slotRole);
  // socket rules
  let g = fresh(20); const give = (id) => C.giveGem(g, id, { silent: true, noAuto: true });
  const fb = give('skill.fireball'), wc = give('skill.whirl_cleave'), md = give('support.minion_damage'), cf = give('support.conv_fire'), ai = give('support.ailment'), aa = give('support.aura_amp'), an = give('skill.anger'), cc = give('support.conv_cold');
  R.sFb = C.socketGem(g, fb, { area: 'main', i: 0, slot: 'skill' });
  R.sMd = C.socketGem(g, md, { area: 'main', i: 0, slot: 'sup', j: 0 }); R.sMdErr = g.lastSocketError;
  R.sCf = C.socketGem(g, cf, { area: 'main', i: 0, slot: 'sup', j: 0 });   // fire → fire: refused
  R.sWc = C.socketGem(g, wc, { area: 'main', i: 3, slot: 'skill' });
  R.sAi = C.socketGem(g, ai, { area: 'main', i: 3, slot: 'sup', j: 0 });   // ailment on physical: refused
  R.sCc = C.socketGem(g, cc, { area: 'main', i: 3, slot: 'sup', j: 0 });   // cold conversion on whirl: fine
  R.sAi2 = C.socketGem(g, ai, { area: 'main', i: 3, slot: 'sup', j: 1 });  // ailment with a conversion in the row: fine
  R.sAa = C.socketGem(g, aa, { area: 'main', i: 5, slot: 'sup', j: 0 });   // aura amp in an empty auto row: refused
  R.sAn = C.socketGem(g, an, { area: 'link', i: 0, slot: 'to' });          // buff as a link target: refused
  // auto socket: a fresh support only goes where it helps; conversions stay in the bag
  const ms = C.giveGem(g, 'support.multi_cast', { silent: true }); R.msAt = C.findSocket(g, ms);
  const cl = C.giveGem(g, 'support.conv_lightning', { silent: true }); R.clAt = C.findSocket(g, cl);
  // link source cycle
  { const it = C.rollItem(g, 'common', 'weapon', { ilvl: 1 }); it.base = 'base.rift_blade'; it.affixes = []; it.unique = null; it.special = null; it.name = C.itemName(it); g.player.equip.weapon = it; C.recomputeStats(g); }
  const tr0 = give('trigger.on_hit'), nova = give('skill.frost_nova');
  C.socketGem(g, tr0, { area: 'link', i: 0, slot: 'trig' }); C.socketGem(g, nova, { area: 'link', i: 0, slot: 'to' }); C.normalizeBuild(g);
  R.from0 = g.player.build.links[0].from; C.cycleLinkSourceAuto(g, 0); R.from1 = g.player.build.links[0].from; C.normalizeBuild(g); R.from1b = g.player.build.links[0].from;
  // the link fed by auto 2 actually fires
  g.enemies.length = 0; for (let i = 0; i < 6; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 20 + i * 4, g.player.y + 10, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
  for (let i = 0; i < 600; i++) C.step(g, {}, 1 / 60);
  R.linkN = g.player.build.links[0].n || 0; R.linkFrom = Object.keys(g.stats.links);
  // scorched on chain lightning
  g = fresh(20); C.setBuild(g, { mains: [{ skill: 'skill.chain_lightning', sup: ['support.scorched'] }], layout: 3 }); C.normalizeBuild(g);
  g.enemies.length = 0; for (let i = 0; i < 5; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 40 + i * 12, g.player.y, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
  for (let i = 0; i < 300; i++) C.step(g, {}, 1 / 60); R.scorch = Math.round(g.stats.dmgBySource['support.scorched'] || 0);
  // blink: manual cast moves the player and hits
  g = fresh(20); C.setBuild(g, { mains: [{ skill: null, sup: [] }, { skill: 'skill.lightning_warp', sup: [] }], layout: 3 }); g.enemies.length = 0;
  const e1 = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 120, g.player.y, { force: true }); e1.hp = e1.maxHp = 1e7; e1.speed = 0; for (let i = 0; i < 40; i++) C.step(g, {}, 1 / 60); const x0 = g.player.x;
  R.warp = C.castMove(g, 1, 0); for (let i = 0; i < 10; i++) C.step(g, {}, 1 / 60); R.warpDx = Math.round(g.player.x - x0); R.warpDmg = Math.round(g.stats.dmgBySource['skill.lightning_warp'] || 0);
  g = fresh(20); C.setBuild(g, { mains: [{ skill: null, sup: [] }, { skill: 'skill.flame_dash', sup: [] }], layout: 3 }); g.enemies.length = 0;
  const e2 = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 100, g.player.y, { force: true }); e2.hp = e2.maxHp = 1e7; e2.speed = 0; for (let i = 0; i < 40; i++) C.step(g, {}, 1 / 60); const x1 = g.player.x;
  C.castMove(g, 1, 0); for (let i = 0; i < 60; i++) C.step(g, {}, 1 / 60); R.dashDx = Math.round(g.player.x - x1); R.dashZones = g.zones.filter((z) => z.kind === 'burning').length + (g.stats.dmgBySource['skill.flame_dash'] ? 100 : 0);
  // contagion spreads on death
  g = fresh(20); C.setBuild(g, { mains: [{ skill: 'skill.contagion', sup: [] }], layout: 3 }); g.enemies.length = 0;
  for (let i = 0; i < 8; i++) { const e = C.spawnEnemy(g, 'enemy.swarm', g.player.x + 60 + (i % 4) * 14, g.player.y + Math.floor(i / 4) * 14, { force: true }); if (e) e.speed = 0; }
  for (let i = 0; i < 400; i++) C.step(g, {}, 1 / 60); R.contKills = g.stats.kills;
  // evolution + fusion + resonance
  g = fresh(20); g.noSpawns = false; C.setBuild(g, { mains: [{ skill: 'skill.fireball', sup: [] }, { skill: null, sup: [] }, { skill: null, sup: [] }, { skill: 'skill.arc_spark', sup: [] }], layout: 3 }); C.normalizeBuild(g); g.evoPaths = { 'skill.fireball': [1, 1] };
  for (let i = 0; i < 60 * 160 && g.state === 'playing' && !(g.evo && g.evo.fusion); i++) C.step(g, C.autopilot(g), 1 / 60);
  R.evo = g.evo ? { stage: g.evo.stage, fusion: g.evo.fusion && g.evo.fusion.key, t: Math.round(g.t) } : null;
  R.evoMods = C.evoMods(g, 'skill.fireball'); R.reso = C.resonance(g);
  for (let i = 0; i < 60 * 8; i++) C.step(g, C.autopilot(g), 1 / 60); R.fusionCasts = g.stats.fusionCasts || 0;
  return R;
}"""

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'Failed to load' not in m.text else None)
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'warning' and 'validation' in m.text else None)
        pg.route('**/version.json*', lambda r: r.fulfill(status=404))
        pg.goto('http://localhost:%d/index.html' % port); pg.wait_for_timeout(1000)
        check('version 0.16.x', '0.16.' in pg.title(), pg.title())
        pg.evaluate("() => window.__evolve.startNewCharacter()")
        R = pg.evaluate(CORE)
        check('slot unlocks 3/4/5/6/7', R['shape'] == [3, 4, 5, 6, 7], R['shape'])
        check('roles', R['roles'] == ['primary', 'move', 'buff', 'primary', 'buff', 'primary', 'buff'], R['roles'])
        check('useless support refused (minion dmg on fireball)', R['sFb'] and not R['sMd'] and R['sMdErr'], R)
        check('same-element conversion refused', not R['sCf'], R)
        check('ailment on physical refused, ok with a conversion', R['sWc'] and not R['sAi'] and R['sCc'] and R['sAi2'], R)
        check('buff support refused in an auto row, buff refused as link target', not R['sAa'] and not R['sAn'], R)
        check('auto socket: multi-cast onto fireball, conversion stays in bag', R['msAt'] and R['msAt']['i'] == 0 and R['clAt'] is None, R)
        check('link source cycles between auto skills', R['from0'] == 'skill.fireball' and R['from1'] == 'skill.whirl_cleave' and R['from1b'] == 'skill.whirl_cleave', R)
        check('link fed by auto 2 fires', R['linkN'] > 0 and any(k.startswith('skill.whirl_cleave') for k in R['linkFrom']), R)
        check('scorched on chain lightning', R['scorch'] > 0, R['scorch'])
        check('lightning warp teleports + hits', R['warp'] and R['warpDx'] > 60 and R['warpDmg'] > 0, R)
        check('flame dash travels + trail', R['dashDx'] > 60 and R['dashZones'] > 0, R)
        check('contagion kills', R['contKills'] >= 3, R['contKills'])
        check('evolution to II + fusion', R['evo'] and R['evo']['fusion'] and R['evo']['stage'].get('skill.fireball') == 2, R['evo'])
        check('fireball path [1,1] = giant + volley mods', R['evoMods'] and R['evoMods']['size'] > 1.5 and R['evoMods']['proj'] == 2, R['evoMods'])
        check('fusion bursts', R['fusionCasts'] >= 1, R['fusionCasts'])
        # --- old save (layout 2, Lv20, three persistent skills) migrates to layout 3
        mig = pg.evaluate("""() => { const E = window.__evolve, C = E.core; const s = JSON.parse(JSON.stringify(E.save));
            const L = s.character.gems.list; const add = (id) => { const u = 'g_' + (900 + L.length); L.push({ uid: u, id, level: 1 }); return u; };
            s.character.level = 20; s.character.build.layout = 2;
            const fb = add('skill.fireball'), lp = add('skill.leap_slam'), a1 = add('skill.anger'), a2 = add('skill.hatred'), a3 = add('skill.wrath'), t = add('trigger.on_kill'), to = add('skill.frost_nova');
            s.character.build.mains = [{ skill: fb, sup: [null, null, null, null], link: { trig: t, to, sup: [null], from: 'skill.fireball' } }, { skill: lp, sup: [null, null], link: null }, { skill: a1, sup: [null], link: null }, { skill: a2, sup: [null], link: null }, { skill: a3, sup: [null], link: null }];
            const r = C.Save.migrateSave ? null : null; const out = E.saves.save(0, s); E.loadCurrent(); E.enterVillage && E.enterVillage();
            const g = E.game, b = g.player.build; return { ok: out.ok, ids: b.mains.map((M) => C.gemId(g, M.skill)), link: [C.gemId(g, b.links[0].trig), C.gemId(g, b.links[0].to), b.links[0].from], layout: E.save.character.build.layout }; }""")
        check('layout 2 save → 3 (persistent rows move, link kept)', mig['ids'][:7] == ['skill.fireball', 'skill.leap_slam', 'skill.anger', None, 'skill.hatred', None, 'skill.wrath'] and mig['link'][0] == 'trigger.on_kill' and mig['layout'] == 3, mig)
        # --- orb screen in the village: evolution chips change the saved path
        pg.evaluate("() => { const E = window.__evolve; E.show('town'); E.openOrbs(); }"); pg.wait_for_timeout(150)
        chip = pg.locator('#oEvo_skill_fireball_01')
        has = chip.count() == 1
        if has: chip.click(); pg.wait_for_timeout(100)
        ep = pg.evaluate("() => (window.__evolve.save.progress.evoPaths || {})['skill.fireball']")
        check('evolution chip saves the path', has and ep == [1, 0], [has, ep])
        check('auto card + resonance line + link card', pg.locator('#oCardPrim .oreso').count() == 1 and pg.locator('#oCardLinks').count() == 1 and pg.locator('#oSrc_0').count() == 1, '')
        pg.screenshot(path=shots + '/v16_orbs_village.png')
        # --- achievements screen has the fusion codex
        pg.evaluate("() => { const E = window.__evolve; E.show('town'); }"); pg.wait_for_timeout(50)
        pg.evaluate("() => document.getElementById('tmAch') && document.getElementById('tmAch').click()"); pg.wait_for_timeout(150)
        check('fusion codex listed', pg.locator('#achList .achsub').count() == 1 and pg.locator('#achList .a').count() >= 15 + 20, pg.locator('#achList .a').count())
        # --- a run HUD shows evolution bars
        pg.evaluate("() => { const E = window.__evolve, C = E.core; E.newRun(9, 'zone.rift_outskirts'); E.setFrozen(true); for (let i = 0; i < 120; i++) C.step(E.game, C.autopilot(E.game), 1 / 60); E.render && E.render(); }")
        pg.evaluate("() => { const E = window.__evolve; E.setFrozen(false); }"); pg.wait_for_timeout(400); pg.evaluate("() => window.__evolve.setFrozen(true)")
        check('HUD evolution bar', pg.locator('#gemrow .evb').count() >= 1, pg.locator('#gemrow').inner_html()[:300])
        pg.screenshot(path=shots + '/v16_hud.png')
        real = [e for e in errs if 'supabase' not in e.lower()]
        check('no console errors / data validation warnings', not real, real[:4])
        # phone orb screen
        ph = b.new_page(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True)
        ph.route('**/version.json*', lambda r: r.fulfill(status=404))
        ph.goto('http://localhost:%d/index.html' % port); ph.wait_for_timeout(1000)
        ph.evaluate("() => { const E = window.__evolve; E.loadCurrent(); E.enterVillage && E.enterVillage(); E.openOrbs(); }"); ph.wait_for_timeout(200)
        ph.screenshot(path=shots + '/v16_orbs_phone.png')
        b.close()
finally:
    srv.kill()
print('%d/%d' % (ok, ok + fail))
sys.exit(1 if fail else 0)
