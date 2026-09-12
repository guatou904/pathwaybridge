"""Strict ingestion and explicit candidate mapping, retaining every input record."""

import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from pathlib import Path

from pathwaybridge import __version__

MODALITIES = {"bulk_rna", "single_cell", "spatial", "metabolomics"}
EFFECTS = {"log2_fold_change", "log_fold_change", "fold_change", "difference", "abundance"}
CONTEXT = ("cell_type", "region", "timepoint", "assay", "compartment")
FIELDS = {
    "entity_id",
    "namespace",
    "species",
    "contrast",
    "effect_type",
    "value",
    "unit",
    "p_value",
    "p_adjusted",
    "p_adjust_method",
    "review_status",
    "note",
    *CONTEXT,
}
REQUIRED = {"entity_id", "namespace", "species", "contrast", "effect_type", "value", "unit"}
MISSING = {"", "NA", "NaN", "nan", "null", "None"}


class InputError(ValueError):
    """An actionable input-contract error."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InputError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        obj = json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise InputError(f"Invalid UTF-8 JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise InputError("Expected a JSON object")
    return obj


def mapping_data() -> tuple[dict, str]:
    data = files("pathwaybridge").joinpath("resources/ppp_mouse.json").read_bytes()
    return read_json(data), digest(data)


def number(value: str, field: str, *, optional=False) -> Decimal | None:
    if optional and value in MISSING:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise InputError(f"{field} must be numeric, got {value!r}") from exc
    if not parsed.is_finite():
        raise InputError(f"{field} must be finite")
    return parsed


def direction(value: str, effect: str) -> str:
    if effect == "abundance":
        return "not_applicable"
    v = number(value, "value")
    baseline = 1 if effect == "fold_change" else 0
    return "higher" if v > baseline else "lower" if v < baseline else "unchanged"


def candidate_mapping(row: dict, mapping: dict) -> tuple[str, list[dict]]:
    if row["species"] != mapping["species"]:
        return "unsupported_species", []
    namespace = row["namespace"]
    if namespace not in {"gene_symbol", "gene_alias", "uniprot", "chebi", "compound_name"}:
        return "unsupported_namespace", []
    if (row["modality"] == "metabolomics") != (namespace in {"chebi", "compound_name"}):
        raise InputError("Metabolomics requires chebi/compound_name; RNA requires a gene namespace")
    candidates = [
        m
        for m in mapping["mappings"]
        if m["namespace"] == namespace and m["input_id"] == row["entity_id"]
    ]
    if not candidates:
        return "unmapped", []
    # Entity ambiguity and one entity participating in multiple reactions are distinct.
    entities = {m["entity_id"] for m in candidates}
    status = (
        "ambiguous"
        if len(entities) > 1
        else "alias"
        if any(m["match_type"] == "alias" for m in candidates)
        else "matched"
    )
    return status, candidates


def load_evidence(manifest_path: Path) -> tuple[list[dict], list[dict], str]:
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_json(manifest_bytes)
    if set(manifest) - {"schema_version", "title", "sources"}:
        raise InputError("Unknown manifest key; expected schema_version, title, sources")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise InputError("schema_version must be 1")
    if not isinstance(manifest.get("title", "PathwayBridge report"), str):
        raise InputError("title must be a string")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise InputError("sources must be a non-empty list")
    rows, provenance, seen_ids = [], [], set()
    for source in sources:
        if not isinstance(source, dict) or set(source) - {
            "source_id",
            "experiment_id",
            "file",
            "modality",
            "columns",
            "constants",
            "delimiter",
        }:
            raise InputError("Invalid source object or unknown source key")
        for key in ("source_id", "experiment_id", "file", "modality"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise InputError(f"source.{key} must be a non-empty string")
        sid = source["source_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", sid) or sid in seen_ids:
            raise InputError(f"source_id must be unique and filename-safe: {sid!r}")
        seen_ids.add(sid)
        if source["modality"] not in MODALITIES:
            raise InputError(f"Unsupported modality: {source['modality']}")
        columns, constants = source.get("columns", {}), source.get("constants", {})
        if not isinstance(columns, dict) or not isinstance(constants, dict):
            raise InputError(f"{sid}: columns/constants must be objects")
        if any(not isinstance(v, str) for v in [*columns.values(), *constants.values()]):
            raise InputError(f"{sid}: column names and constants must be strings")
        unknown = (set(columns) | set(constants)) - FIELDS
        if unknown or set(columns) & set(constants):
            raise InputError(f"{sid}: unknown fields {sorted(unknown)} or column/constant overlap")
        missing = REQUIRED - set(columns) - set(constants)
        if missing:
            raise InputError(f"{sid}: missing field mappings: {', '.join(sorted(missing))}")
        path = manifest_path.parent / source["file"]
        raw = path.read_bytes()
        source_hash = digest(raw)
        delimiter = source.get("delimiter", "\t" if path.suffix.lower() == ".tsv" else ",")
        if delimiter not in {",", "\t"}:
            raise InputError(f"{sid}: delimiter must be comma or tab")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError as exc:
            raise InputError(f"{sid}: input must be UTF-8") from exc
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        headers = reader.fieldnames
        if not headers or any(not h for h in headers) or len(headers) != len(set(headers)):
            raise InputError(f"{sid}: missing, blank or duplicate CSV headers")
        if set(columns.values()) - set(headers):
            raise InputError(f"{sid}: referenced column not present in {headers}")
        count = 0
        for record, original in enumerate(reader, 1):
            if None in original or None in original.values():
                raise InputError(f"{sid} record {record}: wrong number of CSV fields")
            row = {k: original[v].strip() for k, v in columns.items()}
            row.update({k: v.strip() for k, v in constants.items()})
            row.update(
                {
                    "source_id": sid,
                    "experiment_id": source["experiment_id"],
                    "source_file": path.name,
                    "source_sha256": source_hash,
                    "source_record": record,
                    "source_line_end": reader.line_num,
                    "modality": source["modality"],
                    "raw_record": original,
                    "evidence_id": f"{sid}:{record}",
                }
            )
            try:
                validate_row(row)
            except InputError as exc:
                raise InputError(f"{sid} record {record}: {exc}") from exc
            rows.append(row)
            count += 1
        if not count:
            raise InputError(f"{sid}: source contains no evidence records")
        provenance.append(
            {
                "source_id": sid,
                "experiment_id": source["experiment_id"],
                "file": path.name,
                "sha256": source_hash,
                "bytes": len(raw),
                "records": count,
                "columns": columns,
                "constants": constants,
                "delimiter": delimiter,
            }
        )
    return rows, provenance, manifest_bytes.decode("utf-8-sig")


def validate_row(row: dict) -> None:
    for key in REQUIRED:
        if not row.get(key) or row[key] in MISSING:
            raise InputError(f"{key} is required (use explicit 'unknown' for unknown context)")
    if row["effect_type"] not in EFFECTS:
        raise InputError(f"Unsupported effect_type: {row['effect_type']}")
    v = number(row["value"], "value")
    if row["effect_type"] == "fold_change" and v <= 0:
        raise InputError("fold_change must be strictly positive")
    for key in ("p_value", "p_adjusted"):
        row.setdefault(key, "")
        p = number(row[key], key, optional=True)
        if p is not None and not 0 <= p <= 1:
            raise InputError(f"{key} must lie between 0 and 1")
    for key in (*CONTEXT, "p_adjust_method", "review_status", "note"):
        row.setdefault(key, "")
        if row[key] in MISSING:
            row[key] = "unknown" if key != "note" else ""
    if row["review_status"] not in {"unknown", "pending", "accepted", "excluded"}:
        raise InputError("review_status must be unknown, pending, accepted or excluded")
    row["direction"] = direction(row["value"], row["effect_type"])


def analyze(manifest_path: Path) -> dict:
    rows, sources, manifest_text = load_evidence(manifest_path)
    mapping, mapping_hash = mapping_data()
    issues, reaction_evidence = [], []
    origins, semantic = defaultdict(list), defaultdict(list)
    for row in rows:
        status, candidates = candidate_mapping(row, mapping)
        row.update(mapping_status=status, candidates=candidates, mapping_version=mapping["version"])
        origins[(row["source_sha256"], row["source_record"])].append(row["evidence_id"])
        key = tuple(
            row[k]
            for k in (
                "experiment_id",
                "modality",
                "entity_id",
                "namespace",
                "species",
                "contrast",
                "effect_type",
                "unit",
                *CONTEXT,
            )
        )
        semantic[key].append(row["evidence_id"])
        if status != "matched":
            issues.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": status,
                    "detail": "Candidates retained; no automatic resolution.",
                }
            )
        unknown = [k for k in (*CONTEXT, "contrast", "unit") if row[k] == "unknown"]
        if unknown:
            issues.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "unknown_context",
                    "detail": ", ".join(unknown),
                }
            )
        if row["p_adjusted"] not in MISSING and row["p_adjust_method"] == "unknown":
            issues.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "unknown_adjustment",
                    "detail": "Adjusted P value retained; correction method unspecified.",
                }
            )
        if row["review_status"] != "accepted":
            issues.append(
                {
                    "evidence_id": row["evidence_id"],
                    "code": "review_" + row["review_status"],
                    "detail": "Source review status retained, not inferred from mapping.",
                }
            )
        for candidate in candidates:
            for link in candidate["reactions"]:
                reaction_evidence.append(
                    {
                        **{k: v for k, v in row.items() if k not in {"raw_record", "candidates"}},
                        "mapped_entity": candidate["entity_id"],
                        "mapping_match": candidate["match_type"],
                        "mapping_source": candidate["source_url"],
                        "mapping_source_version": candidate["source_version"],
                        "mapping_review": candidate["review_status"],
                        **link,
                    }
                )
    for groups, code in (
        (origins, "duplicate_origin"),
        (semantic, "possible_duplicate_observation"),
    ):
        for ids in groups.values():
            if len(ids) > 1:
                for eid in ids:
                    issues.append(
                        {
                            "evidence_id": eid,
                            "code": code,
                            "detail": " | ".join(ids) + "; retained, not independent replication.",
                        }
                    )
    return {
        "schema_version": 1,
        "software_version": __version__,
        "title": json.loads(manifest_text).get("title", "PathwayBridge report"),
        "manifest_sha256": digest(manifest_path.read_bytes()),
        "mapping_version": mapping["version"],
        "mapping_sha256": mapping_hash,
        "mapping": mapping,
        "sources": sources,
        "evidence": rows,
        "reaction_evidence": reaction_evidence,
        "issues": issues,
        "summary": {
            "records": len(rows),
            "sources": len(sources),
            "mapping_status": dict(Counter(r["mapping_status"] for r in rows)),
            "modalities": dict(Counter(r["modality"] for r in rows)),
            "issue_count": len(issues),
        },
        "interpretation": "Expression and abundance are observations, "
        "not reaction activity or flux. "
        "Candidate links and repeated observations are not independent evidence.",
    }
