"""File-based CLI. Existing directories are never overwritten."""

import argparse
import csv
import json
import sys
from importlib.resources import files
from pathlib import Path

from pathwaybridge import __version__
from pathwaybridge.core import InputError, analyze
from pathwaybridge.report import write_report
from pathwaybridge.viewer import serve_report


def create_demo(out: Path) -> Path:
    if out.exists():
        raise InputError(f"Output already exists; choose a new directory: {out}")
    resource = files("pathwaybridge").joinpath("resources/demo")
    out.mkdir(parents=True)
    for name in ("manifest.json", "rna.csv", "spatial.tsv", "bulk.csv", "metabolites.csv"):
        with (out / name).open("xb") as handle:
            handle.write(resource.joinpath(name).read_bytes())
    return out / "manifest.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Map multi-omics evidence to a bounded mouse PPP reference, offline."
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build"):
        cmd = sub.add_parser(
            name,
            help="Check the input contract"
            if name == "validate"
            else "Write HTML, JSON, TSV, SVG and file hashes",
        )
        cmd.add_argument("--manifest", type=Path, required=True)
        if name == "build":
            cmd.add_argument("--out", type=Path, required=True)
            cmd.add_argument(
                "--open", action="store_true", help="Open the report and keep serving it"
            )
    for name in ("init", "demo"):
        cmd = sub.add_parser(
            name,
            help="Write a synthetic template"
            if name == "init"
            else "Run the packaged synthetic four-modality demo",
        )
        cmd.add_argument("--out", type=Path, required=True)
        if name == "demo":
            cmd.add_argument(
                "--open", action="store_true", help="Open the report and keep serving it"
            )
    viewer = sub.add_parser("serve", help="Reopen a saved report in your browser")
    viewer.add_argument(
        "--report", type=Path, required=True, help="Directory containing report.html"
    )
    viewer.add_argument(
        "--port", type=int, default=0, help="Local port; default chooses a free port"
    )
    viewer.add_argument(
        "--no-open", action="store_true", help="Print the URL without opening a browser"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            serve_report(args.report, port=args.port, open_browser=not args.no_open)
            return 0
        if args.command == "init":
            manifest = create_demo(args.out)
            print(f"Synthetic template: {manifest}")
            return 0
        if args.command == "demo":
            if args.out.exists():
                raise InputError(f"Output already exists; choose a new directory: {args.out}")
            manifest = create_demo(args.out / "inputs")
            report = analyze(manifest)
            write_report(report, args.out / "report")
            print(f"Synthetic demo: {args.out / 'report/report.html'}")
        else:
            report = analyze(args.manifest)
            if args.command == "build":
                write_report(report, args.out)
                print(f"Report: {args.out / 'report.html'}")
        print(json.dumps(report["summary"], ensure_ascii=False))
        if getattr(args, "open", False):
            serve_report(args.out / "report" if args.command == "demo" else args.out)
        return 0
    except (InputError, OSError, UnicodeError, csv.Error) as exc:
        print(f"pathwaybridge: {exc}", file=sys.stderr)
        return 2
