# EVOLVE dev tools

Not part of the game. Kept here so any session can rebuild and test.

- `patches/`: the patch scripts that turned 0.15.1 → 0.15.2 → 0.16.0 (`build160.sh` runs them in order; paths inside point at the session scratchpad, so edit `SP` first).
- `tests/`: Playwright smoke tests (`python3 smoke_p160.py <site dir> <screenshot dir>`), the gem audit (`ev2.py <site> audit.js out.json`, needs `lib.js`) and the balance sim (`sim.js` + `rep.py`).
- Publishing: copy the built page to `index.html`, update `version.json` (version + first `notes` entry), add a `news.json` entry, commit as `Evolve Dev <evolve-dev@users.noreply.github.com>`.
