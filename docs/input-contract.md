# Input contract v1

All inputs are local UTF-8 CSV or TSV (UTF-8 BOM is accepted). Raw analysis objects, counts, microscopy images and raw mass spectra are outside scope. One observation is one source record; headers are unique and every record has the same number of fields. Blank records follow Python CSV parsing and are not observations. Record indexes start at 1 after the header; `source_line_end` records the ending physical line for quoted multiline fields.

The manifest is JSON, with duplicate/unknown keys rejected. Example for an upstream table containing `gene`, `logFC`, `FDR`, `celltype` and `day`:

```json
{
  "schema_version": 1,
  "title": "My PPP evidence",
  "sources": [{
    "source_id": "single-cell-results",
    "experiment_id": "experiment-A",
    "file": "results.csv",
    "modality": "single_cell",
    "columns": {
      "entity_id": "gene",
      "value": "logFC",
      "p_adjusted": "FDR",
      "cell_type": "celltype",
      "timepoint": "day"
    },
    "constants": {
      "species": "10090",
      "namespace": "gene_symbol",
      "contrast": "treated vs control",
      "effect_type": "log2_fold_change",
      "unit": "log2 ratio",
      "p_adjust_method": "BH",
      "region": "unknown",
      "assay": "RNA pseudobulk",
      "compartment": "unknown",
      "review_status": "pending"
    }
  }]
}
```

The contrast above is an example: verify the numerator, reference level, log base and P-value correction from your upstream analysis. A column named `comparison` can contain a time point rather than a group contrast. Never infer semantics from its name alone.

`file` resolves relative to the manifest; absolute paths work locally. Source paths are not copied into reports, but filenames and raw record contents are. `source_id` is unique and matches `[A-Za-z0-9][A-Za-z0-9_.-]{0,79}`. `experiment_id` identifies the underlying experiment, not the output file; reuse it for alternate exports of the same experiment.

`columns` maps normalized field names to literal source headers; `constants` supplies literal **strings**. A normalized field cannot be in both. Missing mapped columns are errors. `delimiter` is optional, comma by default, tab for `.tsv`; supply `"\t"` to override it.

| Field | Contract |
|---|---|
| `entity_id` | Required, non-empty; exact case, no automatic symbol correction |
| `namespace` | Required; `gene_symbol`, `gene_alias`, `uniprot`, `chebi`, `compound_name`; others retained as unsupported |
| `species` | Required taxon ID string; only `10090` maps in this reference |
| `contrast` | Required declared direction/comparison; explicit `unknown` allowed but flagged |
| `effect_type` | Required: `log2_fold_change`, `log_fold_change` (natural log), `fold_change`, `difference`, `abundance` |
| `value`, `unit` | Required finite numeric value and explicit unit; strings are preserved, never rounded |
| `cell_type`, `region`, `timepoint`, `assay`, `compartment` | Separate fields; omitted/blank values become `unknown` |
| `p_value`, `p_adjusted` | Optional finite values in [0,1]; blank/NA/NaN/nan/null/None signify missing |
| `p_adjust_method` | Name and correction scope where known, e.g. `BH across all tested genes`; unknown is flagged if adjusted P is present |
| `review_status` | `pending`, `accepted`, `excluded`, `unknown` (default). Refers to upstream observation review, not mapping review |
| `note` | Optional source limitations or analysis annotations; plain text |

`modality` is source-level: `bulk_rna`, `single_cell`, `spatial`, `metabolomics`. RNA modalities require gene identifiers; metabolomics requires chemical identifiers/names. RNA measurements supplied under a UniProt accession still describe RNA, not protein abundance. Proteomics is deferred.

No row filters or formulas are accepted in the manifest. Export a selected upstream table explicitly if needed, and preserve its upstream provenance. `raw_record` retains every original column and field string, including fields not mapped to the normalized schema. Normalized fields trim boundary whitespace; raw fields do not. File SHA256 identifies the original bytes, including delimiters, encoding marker and line endings.

TSV export prefixes formula-like text with an apostrophe for safer spreadsheet use. Numeric `value`/P columns remain numeric text after validation. Use JSON for exact original strings. Empty source tables, malformed records, invalid numerics and conflicting mappings stop the run with exit 2; unknown IDs/species generate review flags and remain in the report.
