# Reference data and attribution

Retrieved 2026-09-12. Reference package: `mouse-ppp-2026-09-12.1`.

- [UniProt Consortium](https://www.uniprot.org/), release `2026_03`, supplies primary mouse gene names, historical aliases, catalytic reaction descriptions, source evidence codes and Rhea/ChEBI cross-references. [License](https://www.uniprot.org/help/license): CC BY 4.0 for copyrightable database content.
- [ChEBI](https://www.ebi.ac.uk/chebi/about) identifiers are retained as chemical-form identifiers. The linked database is CC BY 4.0. No bulk ChEBI database is bundled.
- [Rhea](https://www.rhea-db.org/) identifiers refer to the reactions cited in UniProt. The bundled snapshot derives from the UniProt response; no Rhea bulk database is copied.
- [Reactome mouse PPP](https://reactome.org/content/detail/R-MMU-71336) is pathway context for research and comparison, not the origin of the bundled reaction data. No KEGG downloads from the private study are redistributed.

Pinned [UniProt response fields](reference/uniprot-2026-09-12.json) include retrieval time, API request URL, release header, original response SHA256, entry versions and selected annotation fields. Sequence and bibliography fields are omitted. A later refetch may change; runtime installs use only the bundled fixed reference.

| Gene | UniProt entry | Reaction |
|---|---|---|
| G6pdx | [Q00612](https://www.uniprot.org/uniprotkb/Q00612/entry) | RHEA:15841 |
| Pgls | [Q9CQ60](https://www.uniprot.org/uniprotkb/Q9CQ60/entry) | RHEA:12556 |
| Pgd | [Q9DCD0](https://www.uniprot.org/uniprotkb/Q9DCD0/entry) | RHEA:10116 |
| Rpia | [P47968](https://www.uniprot.org/uniprotkb/P47968/entry) | RHEA:14657 |
| Rpe | [Q8VEE0](https://www.uniprot.org/uniprotkb/Q8VEE0/entry) | RHEA:13677 |
| Tkt | [P40142](https://www.uniprot.org/uniprotkb/P40142/entry) | RHEA:10508 |
| Taldo1 | [Q93092](https://www.uniprot.org/uniprotkb/Q93092/entry) | RHEA:17053 |
| Ddr2 | [Q62371](https://www.uniprot.org/uniprotkb/Q62371/entry) | Outside-PPP alias counterexample only |

Changes by PathwayBridge contributors: bounded PPP selection, role labels following reference equations, abbreviated display labels, exact-vs-alias distinctions, assay-name candidate lists and review-status fields. Source annotation evidence by similarity remains by similarity; it is not upgraded to direct mouse experimental evidence. This adaptation is distributed under **CC BY 4.0**. The source databases do not endorse PathwayBridge. Code is independently MIT licensed.

The synthetic demo is authored for this project and released under MIT. It contains no private research values. Local real-data verification uses separate ignored paths and must not be copied into the public package or documentation images.
