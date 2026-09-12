"""Explicit developer-only reference fetch; runtime and tests never call the network."""

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENES = ["G6pdx", "Pgls", "Pgd", "Rpia", "Rpe", "Tkt", "Taldo1"]
query = (
    "organism_id:10090 AND reviewed:true AND ("
    + " OR ".join("gene_exact:" + g for g in GENES)
    + ")"
)
url = "https://rest.uniprot.org/uniprotkb/search?" + urllib.parse.urlencode(
    {"query": query, "format": "json", "size": 25}
)
with urllib.request.urlopen(url, timeout=40) as response:
    raw = response.read()
    release = response.headers.get("X-UniProt-Release")
entries = []
for entry in json.loads(raw)["results"]:
    entries.append(
        {k: entry[k] for k in ["primaryAccession", "genes", "entryAudit", "organism", "comments"]}
    )
record = {
    "source_url": url,
    "retrieved_utc": datetime.now(UTC).isoformat(),
    "release": release,
    "response_sha256": hashlib.sha256(raw).hexdigest(),
    "license": "CC-BY-4.0",
    "license_url": "https://www.uniprot.org/help/license",
    "changes": "Selected entry fields; sequence and bibliography omitted.",
    "entries": entries,
}
path = ROOT / "docs/reference/uniprot-2026-09-12.json"
with path.open("x", encoding="utf-8") as out:
    json.dump(record, out, indent=2)
    out.write("\n")
print(f"Reference snapshot: {len(entries)} entries; release {release}")
