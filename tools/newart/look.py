"""Draw a GLB from six fixed named views (the look half of measure-and-look). usage: look.py file.glb out.png [tex|clay|wire]"""
import sys, os, threading, http.server, functools, socketserver
from playwright.sync_api import sync_playwright
glb, out = os.path.abspath(sys.argv[1]), sys.argv[2]; mode = sys.argv[3] if len(sys.argv) > 3 else 'tex'
root = '/home/ubuntu/skyrim-argonia/out/newart'
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
H.log_message = lambda *a, **k: None
srv = socketserver.TCPServer(('127.0.0.1', 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
rel = os.path.relpath(glb, root)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1940, 'height': 856})
    pg.goto(f'http://127.0.0.1:{port}/sheet.html?glb=/{rel}&mode={mode}')
    pg.wait_for_function("document.title==='done'||document.title==='error'", timeout=120000)
    print(pg.title()); pg.wait_for_timeout(500); pg.screenshot(path=out, full_page=True); b.close()
srv.shutdown()
