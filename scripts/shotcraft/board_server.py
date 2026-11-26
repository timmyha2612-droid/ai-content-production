"""Local server for the storyboard app (`sc.py board serve`). Stdlib only.

Binds to 127.0.0.1 only. Every API call needs the per-run token (the X-Board-Token header) and a localhost
Host header, so a web page in another tab can't read the board or post to it.

Routes:
    GET    /                      the app (token injected)
    GET    /api/board             board.view(project)
    POST   /api/refs?shot=N&attr=A&name=F   body: the image bytes -> the new reference
    POST   /api/refs/<id>/rights  body: {"rights": "owned"} -> the reference
    POST   /api/refs/<id>/label   body: {"label": "Editor"} -> the reference
    DELETE /api/refs/<id>
    GET    /files/<asset id>      a board reference image (token as ?t=)
"""
import hmac
import json
import mimetypes
import os
import re
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import Refused, ShotcraftError, board, manifest, paths

APP_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "board", "app.html")
_ID = re.compile(r"^A\d{3,}$")
_HOSTS = ("127.0.0.1", "localhost")


def make_handler(project, token):
    class Handler(BaseHTTPRequestHandler):
        server_version = "shotcraft-board"

        def log_message(self, fmt, *args):  # quiet
            pass

        # -- helpers
        def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode("utf-8")
            elif isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _host_ok(self):
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            return host in _HOSTS

        def _token_ok(self, query=None):
            got = self.headers.get("X-Board-Token") or ((query or {}).get("t") or [""])[0]
            return bool(got) and hmac.compare_digest(str(got), token)

        def _guard(self, query=None):
            if not self._host_ok():
                self._send(403, {"ok": False, "error": "Open the board at http://127.0.0.1."})
                return False
            if not self._token_ok(query):
                self._send(403, {"ok": False, "error": "Missing or wrong board token. Reopen the link sc.py printed."})
                return False
            return True

        def _fail(self, exc):
            code = 400 if isinstance(exc, Refused) else 404 if "No board reference" in str(exc) else 500
            self._send(code, {"ok": False, "error": str(exc)})

        # -- verbs
        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path == "/":
                if not self._host_ok():
                    return self._send(403, "Open the board at http://127.0.0.1.", "text/plain; charset=utf-8")
                if not self._token_ok(q):
                    return self._send(403, "Missing board token. Open the link sc.py board serve printed.",
                                      "text/plain; charset=utf-8")
                with open(APP_FILE, encoding="utf-8") as fh:
                    html = fh.read().replace("__BOARD_TOKEN__", token)
                return self._send(200, html, "text/html; charset=utf-8", {
                    "Content-Security-Policy": "default-src 'self'; img-src 'self' blob: data:; "
                                               "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                                               "font-src https://fonts.gstatic.com; script-src 'unsafe-inline'; "
                                               "connect-src 'self'; frame-ancestors 'none'"})
            if not self._guard(q):
                return
            try:
                if u.path == "/api/board":
                    return self._send(200, {"ok": True, **board.view(project)})
                m = re.match(r"^/files/([A-Za-z0-9]+)$", u.path)
                if m and _ID.match(m.group(1)):
                    a = manifest.find_asset(project, m.group(1))
                    if not a or not isinstance(a.get("board"), dict):
                        return self._send(404, {"ok": False, "error": "Not found."})
                    full = os.path.join(project, a.get("path") or "")
                    if paths.rel_to(project, full) is None or not os.path.isfile(full):
                        return self._send(404, {"ok": False, "error": "Not found."})
                    ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
                    if not ctype.startswith("image/") or ctype == "image/svg+xml":
                        return self._send(404, {"ok": False, "error": "Not found."})
                    with open(full, "rb") as fh:
                        return self._send(200, fh.read(), ctype)
                return self._send(404, {"ok": False, "error": "Not found."})
            except (ShotcraftError, OSError) as exc:
                return self._fail(exc)

        def do_POST(self):
            u = urlparse(self.path)
            if not self._guard():
                return
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                n = 0
            if n > board.MAX_BYTES:
                return self._send(413, {"ok": False, "error": "The file is over 20 MB."})
            body = self.rfile.read(n) if n else b""
            try:
                if u.path == "/api/refs":
                    q = parse_qs(u.query)
                    a = board.add_ref(project, body, (q.get("name") or [""])[0], (q.get("shot") or [""])[0],
                                      (q.get("attr") or [""])[0])
                    return self._send(200, {"ok": True, "id": a["id"], "rights": a["rights"]})
                m = re.match(r"^/api/refs/([A-Za-z0-9]+)/(rights|label)$", u.path)
                if m and _ID.match(m.group(1)):
                    try:
                        value = json.loads(body.decode("utf-8") or "{}").get(m.group(2))
                    except (ValueError, AttributeError):
                        raise Refused("Send JSON like {\"%s\": \"...\"}." % m.group(2))
                    if m.group(2) == "rights":
                        a = board.set_rights(project, m.group(1), value)
                    else:
                        a = board.set_label(project, m.group(1), value)
                    return self._send(200, {"ok": True, "id": a["id"], "rights": a["rights"],
                                            "label": a["board"]["label"]})
                return self._send(404, {"ok": False, "error": "Not found."})
            except ShotcraftError as exc:
                return self._fail(exc)

        def do_DELETE(self):
            u = urlparse(self.path)
            if not self._guard():
                return
            m = re.match(r"^/api/refs/([A-Za-z0-9]+)$", u.path)
            if not (m and _ID.match(m.group(1))):
                return self._send(404, {"ok": False, "error": "Not found."})
            try:
                board.remove_ref(project, m.group(1))
                return self._send(200, {"ok": True})
            except ShotcraftError as exc:
                return self._fail(exc)

    return Handler


def make_server(project, port=0, token=None):
    """A server bound to 127.0.0.1 (port 0 picks a free one). -> (server, token)"""
    token = token or secrets.token_urlsafe(18)
    srv = ThreadingHTTPServer(("127.0.0.1", int(port)), make_handler(project, token))
    srv.daemon_threads = True
    return srv, token


def serve(project, port=8765, open_browser=True):
    try:
        srv, token = make_server(project, port)
    except OSError:
        srv, token = make_server(project, 0)
    url = "http://127.0.0.1:%d/?t=%s" % (srv.server_address[1], token)
    print("Storyboard for %s\nOpen: %s\nStop with Ctrl+C." % (os.path.basename(project), url), flush=True)
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0
