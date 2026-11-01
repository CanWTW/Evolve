"""smoke_p180: difficulty levels + harder baseline, trigger chains (link fed by another link), profile / unique names /
public IDs / friends against an in-memory mock of the Supabase REST API, VFX light layer + decals.
Usage: smoke_p180.py <site> <shots dir>"""
import sys, subprocess, time, json, re
from urllib.parse import urlparse, parse_qs, unquote
from playwright.sync_api import sync_playwright
root, shots = sys.argv[1], sys.argv[2]; port = 8818
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
ok = fail = 0
def check(n, c, i=''):
    global ok, fail
    if c: ok += 1; print('PASS', n)
    else: fail += 1; print('FAIL', n, json.dumps(i, ensure_ascii=False)[:600])

# ---------------- mock PostgREST ----------------
DB = {'characters': [], 'friends': []}; NUID = [0]; NOW = ['2026-10-31T12:00:00.000Z']
def filt(rows, q):
    out = rows
    for k, vs in q.items():
        if k in ('select', 'order', 'limit'): continue
        v = vs[0]
        if k == 'or':
            parts = v.strip('()').split(',')
            def m(r, parts=parts):
                for p in parts:
                    c, op, val = p.split('.', 2)
                    if op == 'eq' and str(r.get(c)) == val: return True
                return False
            out = [r for r in out if m(r)]; continue
        op, val = v.split('.', 1)
        if op == 'eq': out = [r for r in out if str(r.get(k)) == val]
        elif op == 'neq': out = [r for r in out if str(r.get(k)) != val]
        elif op == 'in': S = set(val.strip('()').split(',')); out = [r for r in out if str(r.get(k)) in S]
    return out
def handler(route):
    req = route.request; u = urlparse(req.url); path = u.path; q = parse_qs(u.query); m = req.method
    auth = req.headers.get('authorization', ''); uid = auth.split('tok-')[1] if 'tok-' in auth else None
    body = json.loads(req.post_data) if req.post_data else None
    J = lambda st, obj=None: route.fulfill(status=st, content_type='application/json', body=json.dumps(obj if obj is not None else []))
    if path.startswith('/auth/v1/'):
        NUID[0] += 1; nu = 'u%04d' % NUID[0]
        return J(200, {'access_token': 'tok-' + nu, 'refresh_token': 'r-' + nu, 'expires_in': 3600, 'user': {'id': nu}})
    tbl = path.rsplit('/', 1)[-1]
    if tbl == 'characters':
        T = DB['characters']
        if m == 'GET': return J(200, filt(T, q))
        if m == 'POST':
            b = body
            if any(r['char_id'] == b['char_id'] for r in T): return J(409, {'message': 'duplicate key value violates unique constraint "characters_pkey"'})
            if any(r['name'].lower() == b['name'].lower() for r in T): return J(409, {'message': 'duplicate key value violates unique constraint "characters_name_key"'})
            if any(r['user_id'] == b['user_id'] and r['slot'] == b['slot'] for r in T): return J(409, {'message': 'duplicate key value violates unique constraint "characters_user_id_slot_key"'})
            if b['user_id'] != uid: return J(403, {'message': 'rls'})
            T.append(dict(b, last_seen=NOW[0])); return J(201)
        if m == 'PATCH':
            rows = [r for r in filt(T, q) if r['user_id'] == uid]
            if 'name' in body and any(r['name'].lower() == body['name'].lower() and r not in rows for r in T): return J(409, {'message': 'duplicate key value violates unique constraint "characters_name_key"'})
            for r in rows: r.update(body)
            return J(204 if rows else 200)
        if m == 'DELETE':
            rows = [r for r in filt(T, q) if r['user_id'] == uid]
            DB['characters'] = [r for r in T if r not in rows]; return J(204)
    if tbl == 'friends':
        T = DB['friends']; mine = {r['char_id'] for r in DB['characters'] if r['user_id'] == uid}
        if m == 'GET': return J(200, [r for r in filt(T, q) if r['owner_char'] in mine or r['friend_char'] in mine])
        if m == 'POST':
            if body['owner_char'] not in mine: return J(403, {'message': 'rls'})
            if any(r['owner_char'] == body['owner_char'] and r['friend_char'] == body['friend_char'] for r in T): return J(409, {'message': 'friends_pkey'})
            T.append({'owner_char': body['owner_char'], 'friend_char': body['friend_char'], 'status': 'pending'}); return J(201)
        if m == 'PATCH':
            for r in filt(T, q):
                if r['friend_char'] in mine: r.update(body)
            return J(204)
        if m == 'DELETE':
            rows = [r for r in filt(T, q) if r['owner_char'] in mine or r['friend_char'] in mine]
            DB['friends'] = [r for r in T if r not in rows]; return J(204)
    return J(200, [])

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        def page(w=1280, hh=720):
            ctx = b.new_context(viewport={'width': w, 'height': hh}); pg = ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if (m.type == 'error' and 'Failed to load' not in m.text and 'status of 409' not in m.text) or 'validation' in m.text else None)
            pg.route('**/version.json*', lambda r: r.fulfill(status=404)); pg.route('https://edustzcgqvupqjvneniw.supabase.co/**', handler)
            pg.goto('http://localhost:%d/index.html' % port); pg.wait_for_timeout(900); return ctx, pg, errs
        ctx, pg, errs = page()
        check('version 0.18.0', '0.18.0' in pg.title(), pg.title())
        # ---- difficulty ----
        pg.evaluate("() => window.__evolve.startNewCharacter()")
        D = pg.evaluate("""() => { const E = window.__evolve, C = E.core; const out = {};
          E.newRun(7, 'zone.rift_outskirts'); out.n = { hp: E.game.zone.hpMul, rw: E.game.modReward, diff: E.game.diff };
          out.lock = [E.diffUnlocked(1), E.diffUnlocked(2)]; E.runDiff = 2; out.capped = E.diffNow();
          const s = JSON.parse(JSON.stringify(E.save)); s.progress.bossKills['boss.void_sovereign'] = 1; s.progress.diffBoss = { 1: { 'boss.void_sovereign': 1 } }; E.writeSaveForTest ? E.writeSaveForTest(s) : null;
          return out; }""")
        check('Normal is harder (Z1 hp ×1.15) and diff 0', abs(D['n']['hp'] - 1.15) < 1e-6 and D['n']['diff'] == 0, D)
        check('Hard / Hell locked at the start; selection falls back to Normal', D['lock'] == [False, False] and D['capped'] == 0, D)
        H = pg.evaluate("""() => { const E = window.__evolve, C = E.core; const s = E.save; s.progress.bossKills['boss.void_sovereign'] = 1; s.progress.diffBoss = { 1: { 'boss.void_sovereign': 1 } };
          const out = { unl: [E.diffUnlocked(1), E.diffUnlocked(2)] }; E.runDiff = 2; E.newRun(7, 'zone.rift_outskirts'); const g = E.game;
          out.hell = { hp: g.zone.hpMul, dmg: g.zone.dmgMul, rw: g.modReward, diff: g.diff }; E.runDiff = 1; E.newRun(7, 'zone.ember_canyon'); out.hard = { hp: E.game.zone.hpMul, diff: E.game.diff }; E.show('play'); E.setFrozen(false);
          return out; }""")
        pg.wait_for_timeout(300); H['hud'] = pg.evaluate("() => document.getElementById('zonehud').textContent")
        check('HUD shows the difficulty', 'Hard' in H['hud'] or '困難' in H['hud'], H['hud'])
        check('unlocks follow boss kills', H['unl'] == [True, True], H)
        check('Hell: hp ×5.5, dmg ×2.6, rewards +1.4', abs(H['hell']['hp'] - 1.15 * 5.5) < 1e-6 and abs(H['hell']['dmg'] - 1.15 * 2.6) < 1e-6 and H['hell']['rw'] >= 1.4 and H['hell']['diff'] == 2, H)
        check('Hard Z2 = 4.9 × 2.4', abs(H['hard']['hp'] - 4.9 * 2.4) < 1e-6 and H['hard']['diff'] == 1, H)
        pg.evaluate("() => { const E = window.__evolve; E.loadCurrent(); E.enterVillage && E.enterVillage(); E.show('zones'); E.renderZones && E.renderZones(); }"); pg.wait_for_timeout(200)
        Z = pg.evaluate("() => ({ n: document.querySelectorAll('#zoneList .dbtn').length, on: (document.querySelector('#zoneList .dbtn.on') || {}).id, dis: [...document.querySelectorAll('#zoneList .dbtn')].map((b) => b.disabled) })")
        check('zones screen shows 3 difficulty buttons', Z['n'] == 3, Z)
        pg.screenshot(path=shots + '/v18_zones.png')
        # ---- trigger chains ----
        CH = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.newRun(9, 'zone.rift_outskirts'); const g = E.game; E.setFrozen(true); C.setCharacterLevel(g, 30);
          C.setBuild(g, { mains: [{ skill: 'skill.fireball', sup: [] }], links: [{ from: 'skill.fireball', trig: 'trigger.on_hit', to: 'skill.frost_nova', sup: [] }, { from: null, trig: 'trigger.on_hit', to: 'skill.arc_spark', sup: [] }], layout: 3 }); C.normalizeBuild(g);
          const out = { src1: C.linkSources(g, 1), from1: g.player.build.links[1].from };
          let guard = 0; while (g.player.build.links[1].from !== 'skill.frost_nova' && guard++ < 6) C.cycleLinkSourceAuto(g, 1); out.from1b = g.player.build.links[1].from; C.normalizeBuild(g); out.from1c = g.player.build.links[1].from;
          g.enemies.length = 0; for (let i = 0; i < 8; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 40 + i * 6, g.player.y + 8, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
          for (let i = 0; i < 900; i++) C.step(g, {}, 1 / 60);
          out.n0 = g.player.build.links[0].n || 0; out.n1 = g.player.build.links[1].n || 0; out.depth = g.stats.maxDepthSeen; out.blocked = g.stats.depthBlocked; return out; }""")
        check('link sources include the skill another link casts', 'skill.frost_nova' in CH['src1'] and 'skill.fireball' in CH['src1'], CH)
        check('chained source sticks after normalize', CH['from1b'] == 'skill.frost_nova' and CH['from1c'] == 'skill.frost_nova', CH)
        check('chain fires: Fireball → Frost Nova → Arc Spark (depth 2)', CH['n0'] > 0 and CH['n1'] > 0 and CH['depth'] >= 2, CH)
        pg.evaluate("() => { const E = window.__evolve; E.loadCurrent(); E.enterVillage && E.enterVillage(); const C = E.core, g = E.game; C.setCharacterLevel(g, 30); C.setBuild(g, { mains: [{ skill: 'skill.fireball', sup: [] }], links: [{ from: 'skill.fireball', trig: 'trigger.on_hit', to: 'skill.frost_nova', sup: [] }, { from: 'skill.frost_nova', trig: 'trigger.on_hit', to: 'skill.arc_spark', sup: [] }], layout: 3 }); C.normalizeBuild(g); E.openOrbs(); }")
        pg.wait_for_timeout(200)
        chainUi = pg.evaluate("() => document.querySelectorAll('#oCardLinks .osrc.chain').length")
        check('orb screen marks the chained source', chainUi >= 1, chainUi)
        pg.screenshot(path=shots + '/v18_chain.png')
        # ---- VFX ----
        V = pg.evaluate("""() => { const E = window.__evolve, C = E.core; E.newRun(11, 'zone.rift_outskirts'); const g = E.game; C.setCharacterLevel(g, 30);
          C.setBuild(g, { mains: [{ skill: 'skill.fireball', sup: [] }, { skill: null, sup: [] }, { skill: null, sup: [] }, { skill: 'skill.frost_nova', sup: [] }, { skill: null, sup: [] }, { skill: 'skill.whirl_cleave', sup: [] }], layout: 3 }); C.normalizeBuild(g); E.show('play');
          for (let i = 0; i < 10; i++) { const e = C.spawnEnemy(g, 'enemy.chaser', g.player.x + 30 + i * 9, g.player.y + (i % 3) * 14 - 14, { force: true }); e.hp = e.maxHp = 1e7; e.speed = 0; }
          for (let i = 0; i < 150; i++) C.step(g, {}, 1 / 60); E.setFrozen && E.setFrozen(true); return 1; }""")
        pg.wait_for_timeout(400)
        dec = pg.evaluate("() => (window.__evolve.decals || []).length + ' ' + (window.__evolve.game.fx || []).length")
        pg.screenshot(path=shots + '/v18_vfx.png')
        check('VFX: decals exist after novas / heavy hits', int(dec.split()[0]) > 0, dec)
        real = [e for e in errs if 'supabase' not in e.lower()]
        check('no console errors (page 1)', not real, real[:4])
        ctx.close()
        # ---- profile / unique names / friends ----
        cA, A, eA = page(); cB, B, eB = page()
        for P in (A, B): P.evaluate("() => { const E = window.__evolve; E.startNewCharacter(); E.loadCurrent(); E.enterVillage && E.enterVillage(); E.show('town'); E.openProfile(); }")
        A.wait_for_timeout(1500); B.wait_for_timeout(1500)
        sa = A.evaluate("() => ({ reg: window.__evolve.pfState.reg, id: window.__evolve.save.character.publicId, name: window.__evolve.save.character.name })")
        sb = B.evaluate("() => ({ reg: window.__evolve.pfState.reg, id: window.__evolve.save.character.publicId, name: window.__evolve.save.character.name, warn: (document.querySelector('#pfMe .pfwarn') || {}).textContent || '' })")
        check('first character registers with a 6-char public ID', sa['reg'] == 'ok' and re.match(r'^[A-Z2-9]{6}$', sa['id'] or ''), sa)
        check('same name on another account is refused (case-insensitive unique)', sb['reg'] == 'taken' and sb['name'] == sa['name'], sb)
        B.fill('#pfName', sa['name'].lower() if sa['name'].lower() != sa['name'] else sa['name']); B.click('#pfRename'); B.wait_for_timeout(500)
        m1 = B.evaluate("() => document.getElementById('pfMsg').textContent")
        B.fill('#pfName', 'BetaTester'); B.click('#pfRename'); B.wait_for_timeout(600)
        sb2 = B.evaluate("() => ({ reg: window.__evolve.pfState.reg, name: window.__evolve.save.character.name, id: window.__evolve.save.character.publicId })")
        check('rename to a free name registers', sb2['reg'] == 'ok' and sb2['name'] == 'BetaTester' and any(r['name'] == 'BetaTester' for r in DB['characters']), [sb2, m1])
        # the name survives a village commit (live game copy updated too)
        B.evaluate("() => { window.__evolve.commitVillage && window.__evolve.commitVillage(); }")
        keep = B.evaluate("() => { const E = window.__evolve; E.loadCurrent(); return [E.save.character.name, E.save.character.publicId]; }")
        check('rename + ID persist in the save', keep == ['BetaTester', sb2['id']], keep)
        B.fill('#pfAddId', sa['id'].lower()); B.click('#pfAdd'); B.wait_for_timeout(600)
        check('friend request stored as pending', any(r['owner_char'] == sb2['id'] and r['friend_char'] == sa['id'] and r['status'] == 'pending' for r in DB['friends']), DB['friends'])
        A.evaluate("() => window.__evolve.openProfile()"); A.wait_for_timeout(800)
        inc = A.evaluate("() => [...document.querySelectorAll('#pfFriends .fr')].map((r) => r.textContent)")
        check('incoming request listed for A', any('BetaTester' in t for t in inc), inc)
        A.click('#pfFriends .fr button.primary'); A.wait_for_timeout(700)
        check('accept → accepted', any(r['status'] == 'accepted' for r in DB['friends']), DB['friends'])
        for r in DB['characters']: r['last_seen'] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        B.evaluate("() => window.__evolve.openProfile()"); B.wait_for_timeout(800)
        fl = B.evaluate("() => ({ rows: [...document.querySelectorAll('#pfFriends .fr')].map((r) => r.textContent), on: document.querySelectorAll('#pfFriends .dot.on').length })")
        check('B sees A as an online friend', fl['on'] == 1 and any(sa['name'] in t for t in fl['rows']), fl)
        B.screenshot(path=shots + '/v18_profile.png')
        A.fill('#pfAddId', sa['id']); A.click('#pfAdd'); A.wait_for_timeout(300)
        check('cannot add yourself', 'add yourself' in A.evaluate("() => document.getElementById('pfMsg').textContent") or '自己' in A.evaluate("() => document.getElementById('pfMsg').textContent"))
        real = [e for e in eA + eB if 'supabase' not in e.lower()]
        check('no console errors (profile pages)', not real, real[:4])
        # phone layout
        cP = b.new_context(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True); P = cP.new_page(); P.route('**/version.json*', lambda r: r.fulfill(status=404)); P.route('https://edustzcgqvupqjvneniw.supabase.co/**', handler)
        P.goto('http://localhost:%d/index.html' % port); P.wait_for_timeout(900)
        P.evaluate("() => { const E = window.__evolve; E.startNewCharacter(); E.loadCurrent(); E.enterVillage && E.enterVillage(); E.show('town'); E.openProfile(); }"); P.wait_for_timeout(1200)
        P.screenshot(path=shots + '/v18_profile_phone.png')
        ov = P.evaluate("() => { const s = document.getElementById('profile'); return s.scrollWidth <= s.clientWidth + 2; }")
        check('profile fits a phone in landscape', ov, ov)
        b.close()
finally:
    srv.kill()
print('%d/%d' % (ok, ok + fail)); sys.exit(1 if fail else 0)
