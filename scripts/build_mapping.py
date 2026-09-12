"""Rebuild the bounded reference from a pinned UniProt response and explicit roles."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / "docs/reference/uniprot-2026-09-12.json").read_text(encoding="utf-8"))
entries = {e["primaryAccession"]: e for e in snapshot["entries"]}
# Left/right roles follow the cited equation, not an inferred in-vivo direction.
specs = [
    ("Q00612", "oxidative", "G6P + NADP+ → 6PGL + NADPH + H+", [61548, 58349], [57955, 57783]),
    ("Q9CQ60", "oxidative", "6PGL + H₂O → 6PG + H+", [57955], [58759]),
    ("Q9DCD0", "oxidative", "6PG + NADP+ → Ru5P + CO₂ + NADPH", [58759, 58349], [58121, 57783]),
    ("P47968", "non-oxidative", "R5P ⇌ Ru5P", [58273], [58121]),
    ("Q8VEE0", "non-oxidative", "Ru5P ⇌ X5P", [58121], [57737]),
    ("P40142", "non-oxidative", "S7P + G3P ⇌ R5P + X5P", [57483, 59776], [58273, 57737]),
    ("Q93092", "non-oxidative", "S7P + G3P ⇌ E4P + F6P", [57483, 59776], [16897, 57634]),
]
reactions, mappings, compounds = [], [], {}
for accession, branch, display, left, right in specs:
    entry = entries[accession]
    gene = entry["genes"][0]["geneName"]["value"]
    reaction = next(
        c["reaction"] for c in entry["comments"] if c["commentType"] == "CATALYTIC ACTIVITY"
    )
    rid = next(x["id"] for x in reaction["reactionCrossReferences"] if x["database"] == "Rhea")
    chebi = {x["id"] for x in reaction["reactionCrossReferences"] if x["database"] == "ChEBI"}
    assert all("CHEBI:" + str(c) in chebi for c in left + right)
    url = "https://www.uniprot.org/uniprotkb/" + accession + "/entry"
    version = (
        "UniProt " + snapshot["release"] + "; entry " + str(entry["entryAudit"]["entryVersion"])
    )
    reactions.append(
        {
            "id": rid,
            "gene": gene,
            "branch": branch,
            "equation": reaction["name"],
            "display_equation": display,
            "ec": reaction["ecNumber"],
            "source_url": url,
            "source_version": version,
            "review_status": "source_checked_not_independently_reviewed",
            "reference_evidence": reaction.get("evidences", []),
        }
    )
    for namespace, input_id, match_type in [
        ("gene_symbol", gene, "exact"),
        ("uniprot", accession, "exact"),
        ("gene_alias", gene, "alias"),
        *[("gene_alias", s["value"], "alias") for s in entry["genes"][0].get("synonyms", [])],
    ]:
        mappings.append(
            {
                "namespace": namespace,
                "input_id": input_id,
                "entity_id": "UniProt:" + accession,
                "label": gene,
                "match_type": match_type,
                "source_url": url,
                "source_version": version,
                "review_status": "source_checked_not_independently_reviewed",
                "reactions": [{"reaction_id": rid, "role": "enzyme"}],
            }
        )
    for role, ids in [("substrate", left), ("product", right)]:
        for compound in ids:
            compounds.setdefault(compound, []).append({"reaction_id": rid, "role": role})
# Tkt is a documented historical Ddr2 alias; do not silently discard a non-PPP candidate.
entry = entries["Q62371"]
assert any(x["value"] == "Tkt" for x in entry["genes"][0]["synonyms"])
mappings.append(
    {
        "namespace": "gene_alias",
        "input_id": "Tkt",
        "entity_id": "UniProt:Q62371",
        "label": "Ddr2 (outside this PPP reference)",
        "match_type": "alias",
        "source_url": "https://www.uniprot.org/uniprotkb/Q62371/entry",
        "source_version": "UniProt "
        + snapshot["release"]
        + "; entry "
        + str(entry["entryAudit"]["entryVersion"]),
        "review_status": "source_checked_not_independently_reviewed",
        "reactions": [],
    }
)
aliases = {
    61548: ["G6P"],
    57955: ["6PGL"],
    58759: ["6PG"],
    58121: ["Ru5P", "pentose phosphate"],
    58273: ["R5P", "pentose phosphate"],
    57737: ["X5P", "pentose phosphate"],
    57483: ["S7P"],
    59776: ["G3P"],
    16897: ["E4P"],
    57634: ["F6P"],
    58349: ["NADP+", "NADP(H)"],
    57783: ["NADPH", "NADP(H)"],
}
for compound, links in compounds.items():
    entity = "CHEBI:" + str(compound)
    for namespace, input_id, match in [
        ("chebi", entity, "exact"),
        *[("compound_name", alias, "alias") for alias in aliases[compound]],
    ]:
        mappings.append(
            {
                "namespace": namespace,
                "input_id": input_id,
                "entity_id": entity,
                "label": aliases[compound][0] + " (reaction-specific chemical form)",
                "match_type": match,
                "source_url": "https://www.ebi.ac.uk/chebi/" + entity,
                "source_version": "UniProt "
                + snapshot["release"]
                + " reaction ChEBI cross-reference; local aliases 2026-09-12",
                "review_status": "source_checked_not_independently_reviewed"
                if match == "exact"
                else "assay_identity_review_required",
                "reactions": links,
            }
        )
data = {
    "schema_version": 1,
    "version": "mouse-ppp-2026-09-12.1",
    "species": "10090",
    "name": "Mouse PPP — seven selected reference reactions",
    "license": "CC-BY-4.0",
    "attribution": (
        "Adapted from UniProt Consortium annotations (2026_03), including Rhea "
        "and ChEBI cross-references. Local selection, role labels and assay-name "
        "candidate aliases added by PathwayBridge contributors."
    ),
    "source_snapshot": "docs/reference/uniprot-2026-09-12.json",
    "coverage": (
        "Bounded reference, not exhaustive PPP. Second transketolase reaction, "
        "paralogues, transport and compartment-specific entities are outside this snapshot."
    ),
    "reactions": reactions,
    "mappings": mappings,
}
p = ROOT / "src/pathwaybridge/resources/ppp_mouse.json"
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(reactions)} reactions; {len(mappings)} identifier candidates")
