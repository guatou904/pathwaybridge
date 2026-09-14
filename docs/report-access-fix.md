# Report access fix — 2026-09-14

The previously shared `http://127.0.0.1:8842/report.html` was a temporary development preview. When its process stopped, Safari could no longer connect. The report files remained intact. A successful analysis or unit-test run did not establish that this link would stay available to the user.

Version 0.1.0a3 addresses the delivery gap:

- [Hosted synthetic report](https://guatou904.github.io/pathwaybridge/), independent of the developer's local process. Its build accepts no research-input path and uses only bundled synthetic fixtures.
- A complete `pathwaybridge-demo.zip` with HTML, all seven companion exports/checksums, and opening instructions. Extract the whole ZIP before opening the HTML; the standalone HTML release asset does not include companion files.
- `demo --open` and `build --open` generate and open a report, print its address and explain that the terminal must remain open.
- `serve --report <directory>` reopens saved reports without rebuilding or overwriting them. It binds only to `127.0.0.1`, selects a free port, serves only named report assets, and exposes no directory listing. Ctrl+C closes the viewer and preserves the report.
- Both English and Chinese instructions explain the difference between the hosted example and local analysis, and how to reopen results after stopping the viewer.

## Validation

Local macOS / Python 3.12: 48 tests pass. Added checks request the HTML and every export over HTTP and compare the exact bytes, verify HEAD/download headers, reject unrelated paths and foreign Host headers, exercise CLI errors and browser-launch failure, and confirm that stopping preserves files.

The package installation smoke check now starts the real installed CLI, retrieves every report file, stops it, and starts it again. Both wheel and sdist must pass this check before the release workflow publishes. The publication evidence is attached as `INSTALL_VALIDATION.json`.

Direct file-URL browser automation remains restricted by the in-app browser policy. The ZIP contains self-contained HTML/CSS/JS and companion files; HTTP browser checks and export checks are recorded separately, without claiming an automated file-URL test.

This fixes report access and delivery. It does not expand the seven-reaction mouse PPP reference or establish independent scientific validation.

## macOS startup regression caught before publication

The 0.1.0a2 release candidate passed 47 unit tests in every matrix job, but all three macOS install checks timed out waiting for the viewer's startup URL. Python's default HTTPServer calls `socket.getfqdn()` while binding; the macOS checks took about 35 seconds instead of the local subsecond run. The loopback viewer now binds without reverse DNS. A regression test makes the resolver unavailable and requires startup to succeed. The failed candidate tag is preserved; no 0.1.0a2 release was published. The corrected release is 0.1.0a3.

The original 490-record local input was rebuilt with the access-fix package. Except for the software version, its complete JSON is identical to the earlier report, including every raw value and source reference. No private input or report is published.

## Completed publication checks

- [0.1.0a3 release workflow](https://github.com/guatou904/pathwaybridge/actions/runs/34824761130): all nine OS/Python jobs pass. Downloaded JUnit reports confirm 48 tests, zero failures and zero skips per job. Each job also installs wheel/sdist, serves every export, and restarts the viewer.
- [Hosted demo deployment](https://github.com/guatou904/pathwaybridge/actions/runs/34824756733) succeeds. The hosted HTML and complete ZIP return HTTP 200; version and output hashes were checked.
- Safari on the user's Mac opens the hosted report; Pgd search shows 3 records and Reset restores 20. The final hosted version is 0.1.0a3. The installed report also passed search, spatial/ambiguity filters, empty-state/reset, reaction-to-source navigation, raw-record expansion and an actual TSV download event in the in-app browser.
- Every release payload was downloaded and matched to SHA256SUMS. The downloaded wheel and sdist each passed a fresh installation, analysis, export delivery and viewer restart outside the checkout. The published wheel also reproduced the complete 490-record private report unchanged except for its software version.

[Machine-readable publication and installation evidence](github-access-fix-validation.json). The old development URL is not a persistent entry point; use the hosted demo or start the saved-report viewer explicitly.
