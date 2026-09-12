# Release checklist

Target: exploratory 0.1.0a1, not a validated general pathway inference system.

- [x] Bounded product/input/mapping contracts and explicit non-goals.
- [x] Local four-modality demo; partial-modality support.
- [x] Pinned primary-source annotations and database-license attribution.
- [x] Tests for numerical preservation, reaction identity, malformed data, ambiguity and provenance.
- [x] Real local result-table round trip; no private data included in distribution.
- [x] English/Chinese README, contribution guidance and citation metadata.
- [x] Final Python support matrix and code checks recorded (3.11/3.12/3.13 locally).
- [x] Wheel and sdist build, metadata checks and separate clean installations.
- [x] Final browser QA and artifact contents checked; private inputs excluded.
- [ ] Remote GitHub CI succeeds on the actual release commit.
- [ ] GitHub release created, published downloads reinstalled and hashes checked.
- [ ] PyPI project name and distribution configured, if PyPI publication is approved.
- [ ] Independent human review of 10–20 mappings and two actual user workflows.
- [ ] Comparative task trial against spreadsheet and pyMultiOmics baseline.

Do not mark remote CI, publication, expert review or user validation complete from local tests. The project remains the main active project until its delivery gate is satisfied; do not start FigureGuard implementation from this alpha alone.
