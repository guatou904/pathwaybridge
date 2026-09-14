# Report access fix — 2026-09-14

The previously shared `http://127.0.0.1:8842/report.html` was a temporary development preview. When its process stopped, Safari could no longer connect. The report files remained intact. A successful analysis or unit-test run did not establish that this link would stay available to the user.

Version 0.1.0a2 addresses the delivery gap:

- [Hosted synthetic report](https://guatou904.github.io/pathwaybridge/), independent of the developer's local process. Its build accepts no research-input path and uses only bundled synthetic fixtures.
- A complete `pathwaybridge-demo.zip` with HTML, all seven companion exports/checksums, and opening instructions. Extract the whole ZIP before opening the HTML; the standalone HTML release asset does not include companion files.
- `demo --open` and `build --open` generate and open a report, print its address and explain that the terminal must remain open.
- `serve --report <directory>` reopens saved reports without rebuilding or overwriting them. It binds only to `127.0.0.1`, selects a free port, serves only named report assets, and exposes no directory listing. Ctrl+C closes the viewer and preserves the report.
- Both English and Chinese instructions explain the difference between the hosted example and local analysis, and how to reopen results after stopping the viewer.

## Validation

Local macOS / Python 3.12: 47 tests pass. Added checks request the HTML and every export over HTTP and compare the exact bytes, verify HEAD/download headers, reject unrelated paths and foreign Host headers, exercise CLI errors and browser-launch failure, and confirm that stopping preserves files.

The package installation smoke check now starts the real installed CLI, retrieves every report file, stops it, and starts it again. Both wheel and sdist must pass this check before the release workflow publishes. The publication evidence is attached as `INSTALL_VALIDATION.json`.

Direct file-URL browser automation remains restricted by the in-app browser policy. The ZIP contains self-contained HTML/CSS/JS and companion files; HTTP browser checks and export checks are recorded separately, without claiming an automated file-URL test.

This fixes report access and delivery. It does not expand the seven-reaction mouse PPP reference or establish independent scientific validation.
