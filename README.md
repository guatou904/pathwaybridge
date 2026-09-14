# PathwayBridge

**Put multi-omics observations in a common reaction context, without losing their source.**

[简体中文](README.zh-CN.md) · [Input contract](docs/input-contract.md) · [Mapping policy](docs/mapping-policy.md)

[**0.1.0a2 exploratory prerelease**](https://github.com/guatou904/pathwaybridge/releases/tag/v0.1.0a2). Mouse PPP only: seven selected reference reactions, four kinds of upstream result tables. GitHub publication and downloaded-package installation checks are complete. This is not a complete pathway database; independent scientific review and PyPI publication remain pending.

A gene can move in opposite directions across cell types or spatial regions. A metabolite name can refer to several chemical entities. PathwayBridge keeps those observations separate and makes every candidate mapping inspectable. It reports expression and abundance, **not metabolic flux or a pooled activation score**.

![Synthetic demo — offline evidence report](docs/demo-desktop.png)

## Try it

**[Open the interactive synthetic demo](https://guatou904.github.io/pathwaybridge/)** · [Download the complete demo ZIP](https://guatou904.github.io/pathwaybridge/pathwaybridge-demo.zip)

The hosted report supports search, filters, source inspection and exports. Analyze your own data locally with the CLI below. To read the ZIP offline, extract the whole folder and open `report.html`, keeping the companion files together.

Requires Python 3.11 or newer. Analysis has no runtime package dependencies or network calls; the optional browser viewer connects only to this computer.

```sh
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install "https://github.com/guatou904/pathwaybridge/releases/download/v0.1.0a2/pathwaybridge-0.1.0a2-py3-none-any.whl"
pathwaybridge demo --out demo-run --open
```

The browser opens automatically. Keep the terminal open while viewing; press `Ctrl+C` to stop. To reopen saved results later:

```sh
pathwaybridge serve --report demo-run/report
```

The viewer chooses a free local port and prints its URL. That URL works only while the viewer is running. If no browser opens, copy the printed URL. For generation only, omit `--open`; you can also open `demo-run/report/report.html` directly. Reports are preserved when viewing stops.

 The packaged demo contains **synthetic** bulk RNA, single-cell, spatial and metabolite observations, opposing spatial effects, ambiguous redox/isomer features and unsupported IDs. No private research data are bundled.

## Use your tables

```sh
pathwaybridge init --out my-inputs
# Edit my-inputs/manifest.json to reference your CSV/TSV files.
pathwaybridge validate --manifest my-inputs/manifest.json
pathwaybridge build --manifest my-inputs/manifest.json --out my-report --open
```

The JSON manifest maps existing column names to the evidence schema and explicitly supplies constants such as species and contrast. Files resolve relative to the manifest. Use NCBI taxon `10090` for mouse. Do not relabel a human table as mouse. A single modality works on its own.

Outputs:

| File | Purpose |
|---|---|
| `report.html` | Offline searchable ledger, reaction view, source records and review flags |
| `evidence.json` | Lossless original CSV field strings, normalized observations, all mapping candidates, source hashes |
| `evidence.tsv` | One row per input record |
| `reaction_evidence.tsv` | One row per candidate entity/reaction link; never treat expansions as independent samples |
| `issues.tsv` | Aliases, ambiguity, unsupported IDs/species, missing context, duplicates and review status |
| `mapping.json`, `pathway.svg` | Exact mapping snapshot and reference reaction view |
| `SHA256SUMS` | Hashes for the output files |

Existing output directories are refused, never overwritten. Exit `0` means the input contract was satisfied, **not** that all mappings are resolved or the study is valid. Invalid input/I/O returns `2`. Review flags are always in the output. No records are dropped for missing significance or negative effects.

## Interpretation

- `matched` identifies one entity within this reference; the entity may participate in several reactions. This does not establish experimental correctness or completeness of the mapping database.
- `alias` requires identity review. `ambiguous` retains every known candidate, including candidates outside PPP. Assay names do not establish chemical form or redox state.
- `unmapped` is a coverage/identifier outcome, not absence of expression, abundance or pathway activity. Unsupported species and namespaces are separately labeled.
- Higher/lower is relative to the declared contrast and effect type. Fold-change ratios use 1 as baseline; signed log effects and differences use 0. Absolute abundance has no change direction.
- Cell labels are not physical spatial regions. Unknown assay/compartment remains unknown. Input review states, including `excluded`, stay visible; a successful mapping never clears them.
- Raw P and adjusted P remain separate. No threshold-based significance claim, averaging, cross-modal correlation, enrichment, causal inference or flux estimation is performed.

See [interpretation](docs/interpretation.md) and [mapping policy](docs/mapping-policy.md), including the missing second transketolase reaction and the distinction between formal gene symbols and historical aliases.

See the [0.1.0a2 report-access fix](docs/report-access-fix.md) for the hosted demo, complete ZIP and repeatable local viewer.

## Development

Clone `https://github.com/guatou904/pathwaybridge.git` and enter the repository before running these commands.

```sh
uv sync --locked --no-editable
uv run --no-editable pytest
uv run --no-editable ruff check .
uv run --no-editable ruff format --check src tests scripts
uv run --no-editable python -m build
uv run --no-editable python scripts/package_smoke.py --dist dist --out /tmp/pathwaybridge-install-check
```

Tests cover mapping identity/roles against pinned source annotations, effect semantics, context and precision preservation, malformed inputs, duplicates, escaping, CLI errors and deterministic artifacts. These are engineering checks, not independent expert validation. See the [validation record](docs/validation-record.md) and [release checklist](RELEASE_CHECKLIST.md).

## Why another tool?

[pyMultiOmics](https://github.com/glasgowcompbio/pyMultiOmics) already maps molecules to reactions/pathways; [ReactomeGSA](https://github.com/reactome/ReactomeGSA) supports comparative multi-omics pathway analysis. PathwayBridge tests a narrower workflow: an offline, versioned, row-traceable evidence ledger that retains spatial/cell context and mapping ambiguity. Comparative user testing is still needed; we do not claim superior analysis or first-of-kind integration. [Competitor analysis](COMPETITOR_ANALYSIS.md).

## License and citation

Code: [MIT](LICENSE). Bundled reference annotations are adapted from **UniProt Consortium**, release `2026_03`, under [CC BY 4.0](https://www.uniprot.org/help/license), including Rhea/ChEBI cross-references. Local selection, role labels and assay aliases are documented separately. See [data attribution](docs/data-sources.md) and [CITATION.cff](CITATION.cff). Source databases do not endorse this tool.
