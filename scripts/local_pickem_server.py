"""Local-only static file + Pick Em POST server, for testing before deploy.

Serves the project root like `python3 -m http.server` (so pages, CSS, JS,
images all load the same as before), but also handles POST to
/cgi-bin/submit-picks.py the same way Apache/CGI will in production --
so pickem.js can be tested end-to-end without any server config.

ponytail: dev tool only. The real endpoint on the Linode host is Apache
CGI calling submit_picks.py directly; this script never runs there.
"""
import http.server
import json
import os
import socketserver
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import submit_picks

SUBMIT_PATH = "/cgi-bin/submit-picks.py"


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != SUBMIT_PATH:
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            record = submit_picks.save_picks(payload)
            status, result = 200, {"ok": True, "saved": record}
        except submit_picks.ValidationError as e:
            status, result = 400, {"ok": False, "error": str(e)}
        except Exception:
            status, result = 500, {"ok": False, "error": "unexpected error"}
        body_out = json.dumps(result).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_out)))
        self.end_headers()
        self.wfile.write(body_out)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8791
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"serving project root on http://localhost:{port} (POST {SUBMIT_PATH} wired up)")
        httpd.serve_forever()
