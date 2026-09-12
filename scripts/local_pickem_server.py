"""Local-only static file + Pick Em POST server, for testing before deploy.

Mounts the project root under /premier-league/, the same path prefix the
Linode host serves this app under (a subdirectory of the shared divbox.ai
vhost, not the domain root). Pages use absolute paths like
/premier-league/assets/css/styles.css -- matching that prefix locally means
the exact same HTML works unchanged in both places, no relative-path
juggling needed.

Also handles POST to /premier-league/cgi-bin/submit-picks.py the same way
Apache/CGI will in production, so pickem.js can be tested end-to-end
without any server config.

ponytail: dev tool only. The real endpoint on the Linode host is Apache
CGI calling submit_picks.py directly; this script never runs there. If the
app ever moves to a different path/subdomain, PREFIX is the one thing that
needs to change here (and the hardcoded paths in pickem.html/pickem.js).
"""
import http.server
import json
import os
import socketserver
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import submit_picks

PREFIX = "/premier-league"
SUBMIT_PATH = "/cgi-bin/submit-picks.py"


class Handler(http.server.SimpleHTTPRequestHandler):
    def _strip_prefix(self, path):
        if path.startswith(PREFIX):
            return path[len(PREFIX):] or "/"
        return path

    def translate_path(self, path):
        return super().translate_path(self._strip_prefix(path))

    def do_POST(self):
        if self._strip_prefix(self.path) != SUBMIT_PATH:
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
        print(f"serving project root under http://localhost:{port}{PREFIX}/ (POST {PREFIX}{SUBMIT_PATH} wired up)")
        httpd.serve_forever()
