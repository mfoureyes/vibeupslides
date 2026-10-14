"""Present a deck over a local web server (standard library only).

    vs.py present <deck> [--port N] [--no-open]

Serves one deck folder on 127.0.0.1 and nothing else. Opened over http instead of as a file, YouTube
players work, and the browser remembers for this address what it was allowed (pop-up for the presenter
view, second screen), so the presenter view can put the deck full screen directly.

The server answers GET and HEAD for files inside the folder (and, for a deck that is edited or presented,
POST /__vs/<action> from its own page, see do_POST): no directory listings, no hidden files,
no paths or symbolic links that lead out of the folder, no requests under another host name. It
supports byte ranges, which browsers need to seek in a video.
"""
import json, mimetypes, os, re, signal, socket, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8787                # tried first, so the address (and with it the browser's permissions) stays the same between talks
_RANGE = re.compile(r"bytes=(\d*)-(\d*)$")
_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
          ".json": "application/json", ".svg": "image/svg+xml", ".mp4": "video/mp4", ".m4v": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
          ".ogv": "video/ogg", ".woff2": "font/woff2", ".woff": "font/woff", ".wasm": "application/wasm", ".vtt": "text/vtt", ".glb": "model/gltf-binary"}


def resolve(root, url_path):
    """URL path -> file inside root, or None. root must be a real path."""
    rel = urllib.parse.unquote(url_path.split("?", 1)[0].split("#", 1)[0])
    if "\x00" in rel or "\\" in rel:
        return None
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if any(p == ".." or p.startswith(".") for p in parts):
        return None
    path = os.path.realpath(os.path.join(root, *parts))
    if path != root and not path.startswith(root + os.sep):          # a symbolic link out of the folder
        return None
    return path if os.path.isfile(path) else None


def make_handler(root, index, hosts, api=None, query=""):
    class Handler(BaseHTTPRequestHandler):
        server_version = "vibeupslides"; protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _plain(self, code, text, extra=()):
            body = (text + "\n").encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8"); self.send_header("Content-Length", str(len(body)))
            for k, v in extra: self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD": self.wfile.write(body)

        def _serve(self):
            self.server.vs_asked = True
            if self.headers.get("Host", "").lower() not in hosts:    # a foreign site pointing its own name at 127.0.0.1
                return self._plain(403, "wrong host")
            path = self.path.split("?", 1)[0]
            if path in ("", "/"):
                self.send_response(302); self.send_header("Location", "/" + urllib.parse.quote(index) + query); self.send_header("Content-Length", "0"); self.end_headers(); return
            f = resolve(root, path)
            if not f:
                return self._plain(404, "not found")
            size = os.path.getsize(f); start, end, code = 0, size - 1, 200
            m = _RANGE.match(self.headers.get("Range", "").strip())
            if m and (m.group(1) or m.group(2)):
                if m.group(1):
                    start = int(m.group(1)); end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
                else:
                    start = max(0, size - int(m.group(2)))
                if start > end or start >= size:
                    return self._plain(416, "range not satisfiable", [("Content-Range", f"bytes */{size}")])
                code = 206
            ext = os.path.splitext(f)[1].lower()
            self.send_response(code)
            self.send_header("Content-Type", _TYPES.get(ext) or mimetypes.guess_type(f)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(end - start + 1)); self.send_header("Accept-Ranges", "bytes")
            if code == 206: self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Cache-Control", "no-store")                 # a rebuilt deck shows on reload
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if self.command == "HEAD":
                return
            with open(f, "rb") as fh:
                fh.seek(start); left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(262144, left))
                    if not chunk: break
                    self.wfile.write(chunk); left -= len(chunk)

        def do_GET(self):
            try: self._serve()
            except (BrokenPipeError, ConnectionResetError, socket.timeout): self.close_connection = True      # the browser stopped loading a video

        do_HEAD = do_GET

        def do_POST(self):
            """The editing mode's requests: /__vs/<action> with a JSON body, answered as JSON. Only from the page this
            server itself delivered: same host, same origin, and a content type a foreign page cannot send unasked."""
            def answer(code, data):
                body = json.dumps(data, ensure_ascii=False).encode()
                self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
            self.server.vs_asked = True
            try:
                host = self.headers.get("Host", "").lower(); origin = self.headers.get("Origin")
                m = re.fullmatch(r"/__vs/([a-z]+)", self.path.split("?", 1)[0])
                size = int(self.headers.get("Content-Length") or 0)
                if (not api or not m or host not in hosts or (origin is not None and origin.lower() != "http://" + host)
                        or self.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin"
                        or not self.headers.get("Content-Type", "").lower().startswith("application/json") or size > 2_000_000):
                    self.close_connection = True
                    return answer(403, {"ok": False, "error": "not allowed"})
                try:
                    q = json.loads(self.rfile.read(size) or b"{}")
                    if not isinstance(q, dict): raise ValueError("bad request")
                    res = api(m.group(1), q); answer(200, res)
                    if res.get("stop"):
                        import threading
                        threading.Thread(target=self.server.shutdown, daemon=True).start()
                except (ValueError, KeyError, IndexError, TypeError, OSError) as e:
                    answer(200, {"ok": False, "error": str(e) or "error"})
            except (BrokenPipeError, ConnectionResetError, socket.timeout):
                self.close_connection = True
    return Handler


def start(folder, index, port=None, api=None, query=""):
    """Bind the server. Returns (server, url). port None: the usual port if it is free, any free port otherwise.
    api: a function (action, request dict) -> answer dict for the editing mode; without it the server only reads."""
    root = os.path.realpath(folder)
    class Server(ThreadingHTTPServer):
        daemon_threads = True; allow_reuse_address = True
    server = None
    for cand in ([port] if port else [PORT, 0]):
        try:
            server = Server(("127.0.0.1", cand), BaseHTTPRequestHandler); break
        except OSError as e:
            if port: raise OSError(f"port {port} is not free ({e.strerror or e}). Leave out --port to get a free one.")
    actual = server.server_address[1]
    server.RequestHandlerClass = make_handler(root, index, {f"127.0.0.1:{actual}", f"localhost:{actual}"}, api, query)
    return server, f"http://127.0.0.1:{actual}/{urllib.parse.quote(index)}{query}"


def present(folder, index, port=None, open_browser=True, notes=(), api=None, query="", label="editing"):
    server, url = start(folder, index, port, api, query)
    if api and label == "editing":
        print(f"editing {os.path.basename(os.path.normpath(folder))}: {url}")
        print("Click a text and type; Enter saves, Esc discards. Every change is written into deck.json, the version before it is kept in .history/.")
        print("The command ends when the user presses Done after changing texts (they are then corrected and translated), or with Ctrl-C.")
    else:
        print(f"presenting {os.path.basename(os.path.normpath(folder))}: {url}")
        print("Over http YouTube and Vimeo players work, the presenter view (M) opens without the pop-up block of file:// decks and can put the deck full screen directly.")
    for n in notes: print(n)
    print("Only this folder is served, only to this computer. Stop with Ctrl-C.")
    sys.stdout.flush()
    def stop(*_):
        raise KeyboardInterrupt
    try: signal.signal(signal.SIGTERM, stop)
    except (ValueError, OSError): pass
    def show():
        try:
            import webbrowser; webbrowser.open(url)
        except Exception:
            pass
    if open_browser == "wait":                              # a page from before may be waiting for this server: open one only if none asks
        import threading, time
        server.vs_asked = False
        def later():
            time.sleep(5)
            if not server.vs_asked: show()
        threading.Thread(target=later, daemon=True).start()
    elif open_browser:
        show()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    print("\nstopped."); sys.stdout.flush()
    return 0
