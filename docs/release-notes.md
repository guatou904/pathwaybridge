PathwayBridge 0.1.0a3 fixes report access after a temporary preview server stops.

- A [hosted interactive synthetic demo](https://guatou904.github.io/pathwaybridge/) stays available independently of local development sessions.
- `pathwaybridge demo --out demo-run --open` generates a report and opens a loopback-only browser viewer. Keep the terminal open while viewing; Ctrl+C stops it.
- `pathwaybridge serve --report demo-run/report` reopens existing results without rebuilding or overwriting them. A free local port is selected automatically.
- Download `pathwaybridge-demo.zip`, extract the whole folder, and open `report.html`. It includes every JSON/TSV/SVG export and the output hashes. The standalone `demo.html` is only a visual preview; use the ZIP for companion exports.
- The installation check now verifies actual HTTP delivery of the report and all exports, then stops and restarts the viewer for both wheel and sdist installs.
- Local viewer startup performs no reverse DNS lookup, avoiding a macOS startup delay caught by the release checks. Report section links now scroll to their headings.

Install the attached wheel or source distribution in a fresh Python 3.11+ environment. `INSTALL_VALIDATION.json` and `SHA256SUMS` identify the checked release artifacts. Version 0.1.0a1 remains unchanged.

The analysis scope is unchanged: an exploratory evidence ledger for seven selected mouse PPP reactions, preserving upstream bulk RNA, single-cell, spatial and metabolite observations, original values, context, ambiguity and provenance. Demo values are synthetic. This is not a complete PPP database and does not estimate activity or flux. Independent scientific review and comparative user validation remain pending.
