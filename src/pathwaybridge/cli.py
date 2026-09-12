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
    for name in ("init", "demo"):
        cmd = sub.add_parser(
            name,
            help="Write a synthetic template"
            if name == "init"
            else "Run the packaged synthetic four-modality demo",
        )
        cmd.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
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
        return 0
    except (InputError, OSError, UnicodeError, csv.Error) as exc:
        print(f"pathwaybridge: {exc}", file=sys.stderr)
        return 2
