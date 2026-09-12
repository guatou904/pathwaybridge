import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from pathwaybridge.cli import create_demo, main
from pathwaybridge.core import InputError, analyze, candidate_mapping, direction, mapping_data
from pathwaybridge.report import html_report, tsv, write_report


@pytest.fixture
def manifest(tmp_path):
    return create_demo(tmp_path / "input")


def single(manifest, *, overrides=None, rows=None):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    source = spec["sources"][0]
    path = manifest.parent / source["file"]
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        first = next(reader)
    first.update(overrides or {})
    records = rows or [first]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(records)
    spec["sources"] = [source]
    manifest.write_text(json.dumps(spec), encoding="utf-8")
    return path, records


def test_four_modalities_keep_every_record_and_context(manifest):
    result = analyze(manifest)
    assert result["summary"]["records"] == 20
    assert set(result["summary"]["modalities"]) == {
        "single_cell",
        "spatial",
        "bulk_rna",
        "metabolomics",
    }
    spatial = [r for r in result["evidence"] if r["modality"] == "spatial"]
    assert {(r["region"], r["value"]) for r in spatial} == {
        ("periportal", "-1.30"),
        ("pericentral", "1.90"),
    }
    precise = next(r for r in result["evidence"] if r["modality"] == "bulk_rna")
    assert precise["value"] == "0.000000000000012300"
    assert precise["p_value"] == "1e-300"
    assert all("flux" not in k and "score" not in k for k in result)


def test_identity_ambiguity_is_not_reaction_multiplicity(manifest):
    result = analyze(manifest)
    tkt = [r for r in result["evidence"] if r["entity_id"] == "Tkt"]
    assert [r["mapping_status"] for r in tkt] == ["matched", "ambiguous"]
    assert {m["entity_id"] for m in tkt[1]["candidates"]} == {"UniProt:P40142", "UniProt:Q62371"}
    chebi = next(r for r in result["evidence"] if r["entity_id"] == "CHEBI:58759")
    assert chebi["mapping_status"] == "matched"
    assert len(chebi["candidates"]) == 1
    assert {m["reaction_id"] for m in chebi["candidates"][0]["reactions"]} == {
        "RHEA:12556",
        "RHEA:10116",
    }
    redox = next(r for r in result["evidence"] if r["entity_id"] == "NADP(H)")
    assert redox["mapping_status"] == "ambiguous"
    assert len(redox["candidates"]) == 2


@pytest.mark.parametrize(
    ("value", "effect", "expected"),
    [
        ("0.5", "fold_change", "lower"),
        ("1", "fold_change", "unchanged"),
        ("1.01", "fold_change", "higher"),
        ("-1e-1000", "log2_fold_change", "lower"),
        ("0", "difference", "unchanged"),
        ("2", "abundance", "not_applicable"),
    ],
)
def test_direction_semantics(value, effect, expected):
    assert direction(value, effect) == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"value": "NaN"},
        {"value": "Infinity"},
        {"value": "=1+2"},
        {"p_value": "1.1"},
        {"p_adjusted": "-0.01"},
        {"p_value": "inf"},
        {"value": "0", "effect_type": "fold_change"},
        {"value": "-1", "effect_type": "fold_change"},
        {"effect_type": "activation_score"},
        {"species": ""},
        {"contrast": ""},
        {"review_status": "auto_approved"},
        {"unit": ""},
        {"namespace": "chebi"},
    ],
)
def test_invalid_scientific_input_is_rejected(manifest, overrides):
    single(manifest, overrides=overrides)
    with pytest.raises(InputError):
        analyze(manifest)


def test_partial_modality_and_missing_optional_statistics(manifest):
    single(manifest, overrides={"p_value": "NA", "p_adjusted": "", "region": ""})
    result = analyze(manifest)
    assert result["summary"]["records"] == 1
    assert result["evidence"][0]["p_value"] == "NA"
    assert result["evidence"][0]["region"] == "unknown"


def test_duplicate_input_is_retained_but_flagged(manifest):
    single(manifest)
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    duplicate = deepcopy(spec["sources"][0])
    duplicate["source_id"] = "duplicate"
    spec["sources"].append(duplicate)
    manifest.write_text(json.dumps(spec), encoding="utf-8")
    result = analyze(manifest)
    assert result["summary"]["records"] == 2
    assert sum(i["code"] == "duplicate_origin" for i in result["issues"]) == 2
    assert sum(i["code"] == "possible_duplicate_observation" for i in result["issues"]) == 2


def test_unknown_species_namespace_and_case_are_not_corrected(manifest):
    mapping, _ = mapping_data()
    base = {
        "species": "10090",
        "namespace": "gene_symbol",
        "entity_id": "Pgd",
        "modality": "single_cell",
    }
    assert candidate_mapping(base, mapping)[0] == "matched"
    for overrides, expected in [
        ({"species": "9606"}, "unsupported_species"),
        ({"namespace": "ensembl"}, "unsupported_namespace"),
        ({"entity_id": "PGD"}, "unmapped"),
    ]:
        assert candidate_mapping({**base, **overrides}, mapping) == (expected, [])


def test_source_rows_hashes_and_embedded_newline(manifest):
    path, _ = single(manifest, overrides={"note": 'First line\n"Quoted", second line'})
    raw = path.read_bytes()
    row = analyze(manifest)["evidence"][0]
    assert row["source_record"] == 1
    assert row["source_line_end"] == 3
    assert row["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert row["raw_record"]["note"] == 'First line\n"Quoted", second line'


@pytest.mark.parametrize("content", ["a,a\n1,2\n", "a,b\n1,2,3\n", "", "a,b\n1\n"])
def test_malformed_csv_is_rejected(manifest, content):
    path, _ = single(manifest)
    path.write_text(content, encoding="utf-8")
    with pytest.raises(InputError):
        analyze(manifest)


def test_duplicate_json_keys_and_mistyped_fields(manifest):
    manifest.write_text('{"schema_version":1,"schema_version":1,"sources":[]}', encoding="utf-8")
    with pytest.raises(InputError, match="Duplicate JSON key"):
        analyze(manifest)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(schema_version=True),
        lambda s: s.update(unknown_key=True),
        lambda s: s["sources"][0].update(constants={"species": "10090"}),
        lambda s: s["sources"][0].update(delimiter=";"),
        lambda s: s["sources"][0].update(columns={"value": "absent"}),
        lambda s: s["sources"][0].update(constants={"foo": "unknown"}),
    ],
)
def test_manifest_errors(manifest, mutation):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    mutation(spec)
    manifest.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(InputError):
        analyze(manifest)


def test_column_adapter_constants_and_utf8_bom(manifest):
    spec = {
        "schema_version": 1,
        "sources": [
            {
                "source_id": "upstream",
                "experiment_id": "E1",
                "file": "raw.tsv",
                "modality": "single_cell",
                "columns": {"entity_id": "gene", "value": "logFC", "cell_type": "cluster"},
                "constants": {
                    "namespace": "gene_symbol",
                    "species": "10090",
                    "contrast": "A vs B",
                    "effect_type": "log2_fold_change",
                    "unit": "log2 ratio",
                },
            }
        ],
    }
    manifest.write_text(json.dumps(spec), encoding="utf-8")
    (manifest.parent / "raw.tsv").write_text(
        "gene\tlogFC\tcluster\nPgd\t-0.30\t肝细胞\n", encoding="utf-8-sig"
    )
    row = analyze(manifest)["evidence"][0]
    assert (row["cell_type"], row["value"], row["contrast"]) == ("肝细胞", "-0.30", "A vs B")
    assert row["raw_record"] == {"gene": "Pgd", "logFC": "-0.30", "cluster": "肝细胞"}


def test_report_escapes_html_and_spreadsheet_text(manifest):
    payload = '<img src=x onerror="alert(1)">'
    single(manifest, overrides={"note": payload, "cell_type": "=HYPERLINK(1)", "value": "-0.2"})
    result = analyze(manifest)
    html = html_report(result)
    assert payload not in html
    assert "&lt;img" in html
    assert "Content-Security-Policy" in html
    table = tsv(result["evidence"], ["cell_type", "value"])
    assert "'=HYPERLINK(1)\t-0.2" in table
    assert result["evidence"][0]["raw_record"]["note"] == payload


def test_deterministic_complete_output_and_non_overwrite(manifest, tmp_path):
    result = analyze(manifest)
    output = tmp_path / "report"
    write_report(result, output)
    other = tmp_path / "other"
    write_report(analyze(manifest), other)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {
        p.name: p.read_bytes() for p in other.iterdir()
    }
    with pytest.raises(InputError, match="already exists"):
        write_report(result, output)
    for line in (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        sha, name = line.split(maxsplit=1)
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == sha
    with (output / "reaction_evidence.tsv").open(encoding="utf-8") as h:
        links = list(csv.DictReader(h, delimiter="\t"))
    assert {r["evidence_id"] for r in links} <= {r["evidence_id"] for r in result["evidence"]}


def test_cli_exit_status_and_error_output(manifest, tmp_path, capsys):
    assert main(["validate", "--manifest", str(manifest)]) == 0
    assert main(["build", "--manifest", str(manifest), "--out", str(tmp_path)]) == 2
    assert "already exists" in capsys.readouterr().err
    assert main(["validate", "--manifest", str(tmp_path / "missing")]) == 2


def test_reference_matches_pinned_source_records():
    root = Path(__file__).resolve().parents[1]
    snapshot = json.loads(
        (root / "docs/reference/uniprot-2026-09-12.json").read_text(encoding="utf-8")
    )
    entries = {e["primaryAccession"]: e for e in snapshot["entries"]}
    mapping, _ = mapping_data()
    expected = {
        "G6pdx": "RHEA:15841",
        "Pgls": "RHEA:12556",
        "Pgd": "RHEA:10116",
        "Rpia": "RHEA:14657",
        "Rpe": "RHEA:13677",
        "Tkt": "RHEA:10508",
        "Taldo1": "RHEA:17053",
    }
    assert {r["gene"]: r["id"] for r in mapping["reactions"]} == expected
    for reaction in mapping["reactions"]:
        accession = reaction["source_url"].split("/")[-2]
        entry = entries[accession]
        annotations = [
            c["reaction"] for c in entry["comments"] if c["commentType"] == "CATALYTIC ACTIVITY"
        ]
        source = next(
            a
            for a in annotations
            if any(x["id"] == reaction["id"] for x in a["reactionCrossReferences"])
        )
        assert source["name"] == reaction["equation"]
        assert entry["organism"]["taxonId"] == 10090
        for candidate in mapping["mappings"]:
            if candidate["namespace"] == "chebi" and any(
                r["reaction_id"] == reaction["id"] for r in candidate["reactions"]
            ):
                assert candidate["entity_id"] in {
                    x["id"] for x in source["reactionCrossReferences"]
                }


def test_source_review_exclusion_does_not_disappear(manifest):
    single(manifest, overrides={"review_status": "excluded", "note": "Scale anomaly"})
    result = analyze(manifest)
    assert result["evidence"][0]["review_status"] == "excluded"
    assert result["reaction_evidence"][0]["review_status"] == "excluded"
    assert any(i["code"] == "review_excluded" for i in result["issues"])
    assert "Scale anomaly" in html_report(result)
