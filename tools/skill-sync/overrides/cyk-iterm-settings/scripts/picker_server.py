#!/usr/bin/env python3
"""Local picker only: save an explicit choice, never modify iTerm settings."""
import argparse
from datetime import datetime, timezone
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
from urllib.parse import urlsplit


def atomic_json(path, data):
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def render_picker(template, target, initial):
    if not re.fullmatch(r"[0-9a-f]{6}", initial):
        raise ValueError("Initial color must be six lowercase hex digits")
    display = "~" + target[len(str(Path.home())):] if target == str(Path.home()) or target.startswith(str(Path.home()) + "/") else target
    parts = display.split("/")
    prompt = "/".join([part if part == "~" else part[:1] for part in parts[:-1]] + [parts[-1]])
    # JavaScript data is JSON encoded separately from HTML text.
    script_target = json.dumps(target).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    result = template.replace('var TARGET_PATH = "__TARGET_PATH__";', "var TARGET_PATH = " + script_target + ";")
    for key, value in {"__TARGET_DISPLAY__": display, "__TARGET_BASENAME__": Path(target).name or target, "__PROMPT_DIR__": prompt, "__INITIAL_HEX__": "#" + initial}.items():
        result = result.replace(key, html.escape(value, quote=True))
    if re.search(r"__(?:TARGET|PROMPT|INITIAL)[A-Z_]*__", result):
        raise ValueError("Unresolved picker placeholder")
    return result.encode("utf-8")


def create_server(target, initial, session_dir):
    target = str(Path(target).expanduser().resolve(strict=True))
    if not Path(target).is_dir() or "\n" in target or "\r" in target:
        raise ValueError("Target must be a directory without newlines")
    template = (Path(__file__).resolve().parents[1] / "assets/picker.html").read_text()
    page = render_picker(template, target, initial)
    session_dir = Path(session_dir)
    session_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    token = secrets.token_urlsafe(24)
    prefix = "/" + token + "/"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, mime="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if self.headers.get("Host") != self.server.address:
                self.reply(403, b'{}')
            elif path == prefix:
                self.reply(200, page, "text/html")
            else:
                self.reply(404, b'{}')

        def do_POST(self):
            if self.headers.get("Host") != self.server.address or self.headers.get("Origin") != "http://" + self.server.address:
                self.reply(403, b'{}')
                return
            if self.path != prefix + "choice":
                self.reply(404, b'{}')
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2048:
                    raise ValueError("Invalid payload length")
                data = json.loads(self.rfile.read(length))
                color = data.get("hex", "")
                if data.get("path") != target or not isinstance(color, str) or not re.fullmatch(r"[0-9a-f]{6}", color):
                    raise ValueError("Invalid choice")
            except (ValueError, AttributeError, UnicodeError):
                self.reply(400, b'{}')
                return
            channels = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
            choice = {"path": target, "hex": color, "luminance": round(sum(a * b for a, b in zip(channels, (0.299, 0.587, 0.114))), 1), "session": token, "decidedAt": datetime.now(timezone.utc).isoformat()}
            atomic_json(session_dir / "choice.json", choice)
            self.reply(200, b'{"saved":true}')

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.address = "127.0.0.1:" + str(server.server_port)
    metadata = {"url": "http://" + server.address + prefix, "path": target, "session": token, "choice_file": str((session_dir / "choice.json").resolve())}
    atomic_json(session_dir / "session.json", metadata)
    return server, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--initial", default="1c1c1c")
    parser.add_argument("--session-dir", required=True, type=Path)
    args = parser.parse_args()
    server, metadata = create_server(args.target, args.initial.lower().lstrip("#"), args.session_dir)
    print(json.dumps(metadata, ensure_ascii=False), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
