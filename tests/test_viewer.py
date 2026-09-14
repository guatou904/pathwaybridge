import webbrowser
from http.client import HTTPConnection
from threading import Thread

import pytest

from pathwaybridge.cli import create_demo, main
from pathwaybridge.core import analyze
from pathwaybridge.report import write_report
from pathwaybridge.viewer import REPORT_FILES, report_server, serve_report


@pytest.fixture
def report_dir(tmp_path):
    path = tmp_path / "报告 with spaces"
    write_report(analyze(create_demo(tmp_path / "inputs")), path)
    return path


@pytest.fixture
def viewer(report_dir):
    with report_server(report_dir) as server:
        worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        worker.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            worker.join(timeout=5)


def request(port, path, *, method="GET", headers=None):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_report_and_every_export_served_with_original_bytes(viewer, report_dir):
    for name, content_type in REPORT_FILES.items():
        status, headers, content = request(viewer, f"/{name}")
        assert status == 200
        assert headers["Content-Type"] == content_type
        assert content == (report_dir / name).read_bytes()
        assert headers["Cache-Control"] == "no-store"
    assert request(viewer, "/")[2] == (report_dir / "report.html").read_bytes()
    status, headers, content = request(viewer, "/evidence.tsv", method="HEAD")
    assert status == 200 and content == b""
    assert int(headers["Content-Length"]) == (report_dir / "evidence.tsv").stat().st_size
    assert "attachment" in headers["Content-Disposition"]


def test_viewer_exposes_only_report_exports(viewer, report_dir, tmp_path):
    (report_dir / "private.csv").write_text("PRIVATE", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("SECRET", encoding="utf-8")
    for path in ("/private.csv", "/../secret.txt", "/%2e%2e/secret.txt", "/inputs/", "/missing"):
        assert request(viewer, path)[0] == 404
    assert request(viewer, "/report.html", headers={"Host": "untrusted.example"})[0] == 403
    assert request(viewer, "/evidence.json", method="POST")[0] == 501


def test_cli_reports_missing_report_and_invalid_port(tmp_path, report_dir, capsys):
    assert main(["serve", "--report", str(tmp_path), "--no-open"]) == 2
    assert "No report.html" in capsys.readouterr().err
    assert main(["serve", "--report", str(report_dir), "--port", "65536", "--no-open"]) == 2
    assert "Port must be" in capsys.readouterr().err


def test_browser_failure_keeps_a_printed_url_and_stop_preserves_report(
    report_dir, monkeypatch, capsys
):
    original = {name: (report_dir / name).read_bytes() for name in REPORT_FILES}

    def unavailable(url):
        raise webbrowser.Error("No browser")

    def stop(self, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("pathwaybridge.viewer.webbrowser.open", unavailable)
    monkeypatch.setattr("pathwaybridge.viewer.ThreadingHTTPServer.serve_forever", stop)
    serve_report(report_dir)
    output = capsys.readouterr().out
    assert "Report URL: http://127.0.0.1:" in output
    assert "Browser could not open automatically" in output
    assert "Viewer stopped" in output
    assert {name: (report_dir / name).read_bytes() for name in REPORT_FILES} == original
