import sys, subprocess, time, json
from playwright.sync_api import sync_playwright
root, jsf, outf = sys.argv[1], sys.argv[2], sys.argv[3]; port = sys.argv[4] if len(sys.argv) > 4 else '8781'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', port, '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = b.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/version.json*', lambda r: r.fulfill(status=404))
    pg.goto('http://localhost:%s/index.html' % port); pg.wait_for_timeout(1000)
    pg.evaluate("() => window.__evolve.startNewCharacter()")
    pg.set_default_timeout(0)
    pg.evaluate("() => { " + open("lib.js").read() + " }")
    res = pg.evaluate("() => { " + open(jsf).read() + " }")
    json.dump(res, open(outf, 'w'), ensure_ascii=False, indent=0)
    print('ok', 'errs', errs[:5])
    b.close()
finally: srv.kill()
