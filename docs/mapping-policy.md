# Mapping policy

The bundled reference is `mouse-ppp-2026-09-12.1`, derived from UniProt `2026_03` and pinned by SHA256 in every report. It contains seven selected mouse reaction records (G6pdx, Pgls, Pgd, Rpia, Rpe, Tkt, Taldo1). It is **not an exhaustive PPP model**: the second transketolase reaction, alternative enzymes, transport, PRPP and redox-system branches are not included. No gene or chemical compartment is inferred from pathway membership.

Formal `gene_symbol` matches use the selected UniProt primary gene name, case-sensitively. `gene_alias` searches primary names plus the explicitly included historical aliases. This avoids silently interpreting a historical alias as a formal symbol. For example, `Tkt` in `gene_symbol` identifies UniProt P40142; in `gene_alias` it has two known candidates: P40142 (Tkt) and Q62371 (Ddr2). The latter remains in JSON and the ledger with no PPP link. This small reference is not a complete global synonym registry.

`G6pd` in `gene_alias` is a candidate for `G6pdx` from its source annotation. It is not silently substituted in `gene_symbol`. UniProt accession inputs are exact, with no automatic isoform stripping. Unsupported namespaces, including Ensembl and Entrez in this alpha, remain unsupported instead of being guessed.

Chemical mappings accept the specific ChEBI forms cited by the source reaction annotations. Conjugate acids/bases, anomers and redox states are not automatically merged. Thus a correct chemical ID can still be outside this limited reference. Local labels such as `G6P`, `R5P`, `Ru5P` and `NADP(H)` are **assay-name candidates**, not a global synonym resource. They require identity/form review. `NADP(H)` retains both oxidized/reduced candidates; `pentose phosphate` retains three isomer candidates. Actual assay annotations such as `NADP(H)-1` stay unmapped until their identity is explicitly curated.

| Status | Meaning |
|---|---|
| `matched` | One entity matched exactly within this bounded reference; no claim of experimental validation |
| `alias` | One candidate entity found via an explicit alias; verify the source/assay |
| `ambiguous` | More than one candidate entity; retain all, including outside-pathway candidates |
| `unmapped` | Supported species/namespace, ID outside the snapshot |
| `unsupported_species` | No species conversion performed |
| `unsupported_namespace` | No namespace conversion performed |

Entity ambiguity differs from reaction multiplicity. A unique 6PG entity participates in both the Pgls and Pgd reaction records; it remains `matched` and produces two reaction links. Expansions do not duplicate the original observation count. Substrate/product roles follow the source equation as written; for reversible reactions these are display roles, not an observed in-vivo direction.

Every mapping has an input namespace/ID, candidate entity, source URL/version, match type, review status, and reaction/role list. Every reaction retains the original evidence codes, including annotations by similarity. `source_checked_not_independently_reviewed` means checked against the pinned source by this implementation; it does not mean an independent scientist has reviewed the mapping. User `review_status=accepted` applies only to the source observation and cannot resolve mapping ambiguity.

Default behavior retains every observation. Identical file-hash/record origins and repeated experiment/entity/context observations are flagged, not silently discarded or counted as replication. Counts in the reference view include pending and excluded observations and ambiguous links. Review the ledger before scientific interpretation.

The frozen input reference and `scripts/build_mapping.py` make the selection reproducible. Changing the mapping requires source checks, explicit coverage decisions, tests, a new version identifier and updated attribution. Runtime commands never query or update external databases.
