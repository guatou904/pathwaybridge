"""Deterministic offline output. Escape source text at every HTML boundary."""

import csv
import hashlib
import io
import json
from collections import Counter
from html import escape
from importlib.resources import files
from pathlib import Path

from pathwaybridge.core import InputError


def e(value) -> str:
    return escape(str(value), quote=True)


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def tsv(rows: list[dict], fields: list[str]) -> str:
    """Escape formula-like text for spreadsheet opening; raw strings remain in JSON."""
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        values = {}
        for key in fields:
            value = str(row.get(key, ""))
            if key not in {"value", "p_value", "p_adjusted"} and value.lstrip().startswith(
                ("=", "+", "-", "@")
            ):
                value = "'" + value
            values[key] = value
        writer.writerow(values)
    return buf.getvalue()


def reaction_svg(report: dict) -> str:
    reactions = report["mapping"]["reactions"]
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 770" role="img" '
        'aria-labelledby="map-title map-desc">',
        '<title id="map-title">PPP reference reactions and observed evidence</title>',
        '<desc id="map-desc">Seven selected reactions, grouped by branch. '
        "Arrows describe reference chemistry, not measured flux. "
        "Counts include candidate links.</desc>",
        '<rect width="1000" height="770" rx="16" fill="#f4f7f4"/>',
    ]
    for index, reaction in enumerate(reactions):
        y = 18 + index * 107
        rid = reaction["id"]
        linked = [r for r in report["reaction_evidence"] if r["reaction_id"] == rid]
        count = len({r["evidence_id"] for r in linked})
        color = "#1b6456" if count else "#69756f"
        elements.append(
            f'<a href="#rxn-{e(rid)}"><rect x="16" y="{y}" width="968" height="94" '
            f'rx="10" fill="white" stroke="#d9e2da"/>'
            f'<text x="34" y="{y + 25}" font-family="sans-serif" font-size="13" '
            f'fill="{color}">{e(reaction["branch"].upper())} · {e(rid)}</text>'
            f'<text x="34" y="{y + 58}" font-family="sans-serif" font-weight="bold" '
            f'font-size="21" fill="#18342d">{e(reaction["gene"])}</text>'
            f'<text x="165" y="{y + 54}" font-family="sans-serif" font-size="16" '
            f'fill="#18342d">{e(reaction["display_equation"])}</text>'
            f'<text x="165" y="{y + 77}" font-family="sans-serif" font-size="12" '
            f'fill="#52635b">{e(reaction["ec"])} · reference chemistry</text>'
            f'<text x="950" y="{y + 48}" text-anchor="end" font-family="sans-serif" '
            f'font-size="25" fill="{color}">{count}</text>'
            f'<text x="950" y="{y + 70}" text-anchor="end" font-family="sans-serif" '
            f'font-size="11" fill="#52635b">records</text></a>'
        )
    elements.append("</svg>")
    return "".join(elements)


def html_report(report: dict) -> str:
    resource = files("pathwaybridge").joinpath("resources")
    css, js = (
        resource.joinpath("report.css").read_text(encoding="utf-8"),
        resource.joinpath("report.js").read_text(encoding="utf-8"),
    )
    import base64

    script_hash = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    summary, evidence = report["summary"], report["evidence"]
    issues_by_row = {}
    for issue in report["issues"]:
        issues_by_row.setdefault(issue["evidence_id"], []).append(issue["code"])
    rows = []
    for row in evidence:
        contexts = " · ".join(f"{k}: {row[k]}" for k in ("cell_type", "region", "timepoint"))
        candidates = "<br>".join(e(m["entity_id"]) for m in row["candidates"]) or "—"
        badges = " ".join(
            f'<span class="badge">{e(x)}</span>' for x in issues_by_row.get(row["evidence_id"], [])
        )
        source_text = json_text(row["raw_record"])
        rows.append(
            f'<tr id="ev-{e(row["evidence_id"])}" data-modality="{e(row["modality"])}" '
            f'data-status="{e(row["mapping_status"])}">'
            f"<td><strong>{e(row['entity_id'])}</strong><small>{e(row['namespace'])}</small>"
            f"<small>{e(row['modality'])}</small></td>"
            f"<td>{e(row['contrast'])}<small>{e(contexts)}</small>"
            f"<small>experiment: {e(row['experiment_id'])} · species: {e(row['species'])}</small>"
            f"<small>assay: {e(row['assay'])} · compartment: {e(row['compartment'])}</small></td>"
            f'<td><strong class="{e(row["direction"])}">{e(row["value"])}</strong>'
            f"<small>{e(row['effect_type'])} · {e(row['unit'])}</small>"
            f"<small>{e(row['direction'])}</small></td>"
            f"<td>P: {e(row['p_value']) or '—'}<small>Adjusted P: "
            f"{e(row['p_adjusted']) or '—'}</small><small>{e(row['p_adjust_method'])}</small></td>"
            f"<td>{e(row['mapping_status'])}<small>{candidates}</small>{badges}</td>"
            f"<td><details><summary>{e(row['source_id'])} · record {row['source_record']}</summary>"
            f"<small>{e(row['source_file'])} · line end {row['source_line_end']}</small>"
            f"<small>SHA256: {e(row['source_sha256'])}</small>"
            f"<small>Source review: {e(row['review_status'])}</small>"
            f"<p>{e(row['note'])}</p><pre>{e(source_text)}</pre></details></td></tr>"
        )
    reaction_cards = []
    for reaction in report["mapping"]["reactions"]:
        rid = reaction["id"]
        linked = [r for r in report["reaction_evidence"] if r["reaction_id"] == rid]
        items = (
            "".join(
                f'<li><a href="#ev-{e(r["evidence_id"])}">{e(r["evidence_id"])}</a> '
                f"· {e(r['mapped_entity'])} · {e(r['role'])} · {e(r['mapping_status'])} "
                f"· {e(r['modality'])} · {e(r['cell_type'])} / {e(r['region'])} "
                f"· {e(r['timepoint'])} · {e(r['contrast'])} "
                f'· <span class="{e(r["direction"])}">{e(r["value"])} '
                f"{e(r['effect_type'])}</span> · source review: {e(r['review_status'])}</li>"
                for r in linked
            )
            or "<li>No input observation mapped. This does not mean no activity.</li>"
        )
        reaction_cards.append(
            f'<details class="reaction" id="rxn-{e(rid)}"><summary>'
            f"<strong>{e(reaction['gene'])}</strong> "
            f"· {e(reaction['display_equation'])} <span>{len({r['evidence_id'] for r in linked})}"
            f' records</span></summary><p><a href="{e(reaction["source_url"])}">'
            f"{e(rid)}</a> · {e(reaction['source_version'])} · {e(reaction['review_status'])}</p>"
            f"<p>{e(reaction['equation'])}</p><ul>{items}</ul></details>"
        )
    statuses = Counter(row["mapping_status"] for row in evidence)
    pending = sum(1 for row in evidence if row["mapping_status"] != "matched")

    def options(values):
        return "".join(f'<option value="{e(v)}">{e(v)}</option>' for v in sorted(values))

    sources = "".join(
        f"<li><strong>{e(s['source_id'])}</strong> · {e(s['file'])} · {s['records']} records"
        f"<small>{e(s['sha256'])}</small></li>"
        for s in report["sources"]
    )
    values = {
        "script_hash": script_hash,
        "css": css,
        "js": js,
        "title": e(report["title"]),
        "software_version": e(report["software_version"]),
        "records": len(evidence),
        "source_count": summary["sources"],
        "issue_count": summary["issue_count"],
        "pending": pending,
        "svg": reaction_svg(report),
        "reactions": "".join(reaction_cards),
        "modality_options": options(summary["modalities"]),
        "status_options": options(statuses),
        "rows": "".join(rows),
        "mapping_version": e(report["mapping_version"]),
        "mapping_sha256": e(report["mapping_sha256"]),
        "sources": sources,
    }
    return resource.joinpath("report.html").read_text(encoding="utf-8").format_map(values)


def write_report(report: dict, out: Path) -> None:
    # Compute everything before creating output; never overwrite or delete user files.
    fields = [
        "evidence_id",
        "entity_id",
        "namespace",
        "species",
        "modality",
        "experiment_id",
        "cell_type",
        "region",
        "timepoint",
        "assay",
        "compartment",
        "contrast",
        "effect_type",
        "value",
        "unit",
        "direction",
        "p_value",
        "p_adjusted",
        "p_adjust_method",
        "review_status",
        "mapping_status",
        "mapping_version",
        "source_id",
        "source_file",
        "source_record",
        "source_line_end",
        "source_sha256",
        "note",
    ]
    output = {
        "report.html": html_report(report),
        "evidence.json": json_text(report),
        "evidence.tsv": tsv(report["evidence"], fields),
        "reaction_evidence.tsv": tsv(
            report["reaction_evidence"],
            [
                *fields,
                "reaction_id",
                "role",
                "mapped_entity",
                "mapping_match",
                "mapping_source",
                "mapping_source_version",
                "mapping_review",
            ],
        ),
        "issues.tsv": tsv(report["issues"], ["evidence_id", "code", "detail"]),
        "mapping.json": json_text(report["mapping"]),
        "pathway.svg": reaction_svg(report),
    }
    if out.exists():
        raise InputError(f"Output already exists; choose a new directory: {out}")
    out.mkdir(parents=True)
    for name, text in output.items():
        with (out / name).open("x", encoding="utf-8", newline="") as handle:
            handle.write(text)
    hashes = "".join(
        f"{hashlib.sha256(text.encode()).hexdigest()}  {name}\n"
        for name, text in sorted(output.items())
    )
    (out / "SHA256SUMS").write_text(hashes, encoding="utf-8")
