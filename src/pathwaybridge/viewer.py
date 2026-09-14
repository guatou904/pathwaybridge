"""Explicit, loopback-only report viewing with a user-controlled lifetime."""

import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from urllib.parse import urlsplit

from pathwaybridge.core import InputError

REPORT_FILES = {
    "report.html": "text/html; charset=utf-8",
    "evidence.json": "application/json; charset=utf-8",
    "evidence.tsv": "text/tab-separated-values; charset=utf-8",
    "reaction_evidence.tsv": "text/tab-separated-values; charset=utf-8",
    "issues.tsv": "text/tab-separated-values; charset=utf-8",
    "mapping.json": "application/json; charset=utf-8",
    "pathway.svg": "image/svg+xml",
    "SHA256SUMS": "text/plain; charset=utf-8",
}


class LocalReportServer(ThreadingHTTPServer):
    def server_bind(self):
        # HTTPServer normally reverse-resolves its address. A loopback viewer needs no
        # DNS, and that lookup can block startup on Macs with an unavailable resolver.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def report_server(report_dir: Path, port: int = 0) -> ThreadingHTTPServer:
    root = report_dir.resolve()
    if not (root / "report.html").is_file():
        raise InputError(f"No report.html in {report_dir}; run build or demo first")
    if not 0 <= port <= 65535:
        raise InputError("Port must be between 0 and 65535 (0 chooses a free port)")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_report(head_only=False)

        def do_HEAD(self):
            self.send_report(head_only=True)

        def send_report(self, *, head_only):
            host = self.headers.get("Host", "")
            allowed_hosts = {f"127.0.0.1:{self.server.server_port}"}
            if host not in allowed_hosts:
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            name = "report.html" if path == "/" else path.removeprefix("/")
            if name not in REPORT_FILES:
                self.send_error(404)
                return
            file = root / name
            # Never expose a directory listing, neighboring inputs, or linked files.
            if file.is_symlink() or not file.is_file():
                self.send_error(404)
                return
            try:
                content = file.read_bytes()
            except OSError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", REPORT_FILES[name])
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if name not in {"report.html", "pathway.svg"}:
                self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.end_headers()
            if not head_only:
                self.wfile.write(content)

        def log_message(self, format, *args):
            pass

    return LocalReportServer(("127.0.0.1", port), Handler)


def serve_report(report_dir: Path, *, port: int = 0, open_browser: bool = True) -> None:
    with report_server(report_dir, port) as server:
        url = f"http://127.0.0.1:{server.server_port}/report.html"
        print(f"Report URL: {url}", flush=True)
        print("Keep this terminal open while viewing. Press Ctrl+C to stop.", flush=True)
        print("To reopen later, run pathwaybridge serve --report with this directory:", flush=True)
        print(report_dir.resolve(), flush=True)
        if open_browser:
            try:
                opened = webbrowser.open(url)
            except (webbrowser.Error, OSError):
                opened = False
            if not opened:
                print(
                    "Browser could not open automatically; open the Report URL above.", flush=True
                )
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            print("\nViewer stopped. Your report files are saved and can be reopened.", flush=True)
