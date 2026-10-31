#!/usr/bin/env python3
"""EVOLVE v0.16.0 part F: leaderboards keep one best record per character (rift_scores.char_id, migration rift_scores_per_character).
Usage: patch_p160e.py in.html out.html"""
import sys, json
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
EN = json.load(open(src + '.en.json'))


def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit('expected %d match(es), got %d for: %r' % (count, n, old[:100]))
    h = h.replace(old, new)


rep("async function submitScore(gg, s) {",
    "function charIdOf(s) { return String((s && s.character && s.character.id) || ('slot' + SLOT)).slice(0, 40); }   // v0.16: one leaderboard record per character\n"
    "async function submitScore(gg, s) {")
rep("build: buildTag(gg), version: C.VERSION }", "build: buildTag(gg), version: C.VERSION, char_id: charIdOf(s) }", 2)
rep("'&user_id=eq.' + sbSess.uid", "'&user_id=eq.' + sbSess.uid + '&char_id=eq.' + encodeURIComponent(row.char_id)", 2)
rep("on_conflict=user_id,kind,period'", "on_conflict=user_id,kind,period,char_id'", 2)
open(dst, 'w', encoding='utf-8').write(h)
json.dump(EN, open(dst + '.en.json', 'w'), ensure_ascii=False)
print('ok per-character leaderboard')
h = open(dst, encoding='utf-8').read()
rep("'leap', 'slam', 'dash', 'summon', 'buff'];", "'leap', 'slam', 'dash', 'summon', 'buff', 'blink'];   // v0.16 spell movement")
open(dst, 'w', encoding='utf-8').write(h)
