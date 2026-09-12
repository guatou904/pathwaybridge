# Validation record — 2026-09-12

Scope: local exploratory 0.1.0a1. Remote execution, public release, independent scientific review and comparative user trials are not established by these checks.

## Executed checks

| Check | Actual result |
|---|---|
| macOS arm64, Python 3.11.16 | 43 tests pass |
| macOS arm64, Python 3.12.14 | 43 tests pass |
| macOS arm64, Python 3.13.9 | 43 tests pass |
| Source checks | Ruff lint and formatting pass; actionlint validates both workflow files |
| Scientific data contract | Exact values and very small P values retained; effect-type baselines, opposing contexts, ambiguous IDs, out-of-pathway alias candidates, repeated origins and excluded records tested |
| Source mapping verification | Seven reaction identities/equations and chemical cross-references checked against pinned UniProt annotations; this is not an independent human gold set |
| Real local input | 490 records from two upstream result tables; every original field string, normalized mapped value, source record index and file SHA256 checked |
| Browser, desktop | 1280×720; report layout, Pgd search, spatial filter, three ambiguous observations, empty state, Reset, reaction-to-source navigation and expandable raw source verified |
| Browser, mobile | 390×844; page width equals viewport width; wide reaction view and table scroll within their own panels |
| Browser errors | No page error/warning logs observed during the final synthetic report checks |

[Desktop preview](demo-desktop.png) · [Mobile preview](demo-mobile.png) · [Shareable real-input verification summary](real-input-validation.json).

The real data remain in ignored local paths. Their report includes 304 exact matches, 18 alias candidates and 168 unmapped observations; nothing was dropped. Those counts reflect this limited reference and the supplied tables, not coverage of the entire PPP or a biological finding. The shareable verification summary contains counts and check descriptions only.

`artifacts/tests-py311.xml`, `artifacts/tests-py312.xml`, `artifacts/tests-py313.xml` retain local JUnit evidence. Tests ran against fresh non-editable installed packages, including an explicit reinstall of the final Python 3.12 package. This avoids a local environment issue with editable `.pth` loading.

## Distribution verification

Both wheel and sdist passed Twine metadata validation and separate clean installations outside the checkout on Python 3.12.14. The installation script executes version/demo/validate/build, checks installed dependencies and verifies output hashes. The exact distribution checks are recorded in the install-results JSON outside the checkout and copied into `docs/package-install-validation.json`. The record names each artifact and its SHA256. It is excluded from the sdist to avoid embedding an artifact's own hash inside itself. No private inputs, local reports or virtual environments are included in either distribution. This does not claim GitHub or PyPI publication.

## Reproduce

```sh
uv sync --locked --no-editable --reinstall-package pathwaybridge --python 3.12
uv run --no-editable pytest
uv run --no-editable ruff check .
uv run --no-editable ruff format --check src tests scripts
uv run --no-editable python -m build
uv run --no-editable twine check dist/*.whl dist/*.tar.gz
uv run --no-editable python scripts/package_smoke.py --dist dist --out /tmp/pathwaybridge-smoke-new
```

Use a new output directory for each install check. Separate `UV_PROJECT_ENVIRONMENT` directories were used for Python 3.11 and 3.13. Network is only needed to fetch build/dev tools; normal CLI execution and tests use the packaged reference.

Remaining: remote Linux/Windows CI, actual release/download verification, independent human review of mapping correctness/coverage, and two actual users completing the traceability workflow. No public URL or claim of external validation is fabricated.

Build compatibility: the initial Hatchling 1.32.0 build selected metadata 2.5, which the locked Twine version rejected. The final configuration explicitly emits metadata 2.4 for both wheel and sdist and pins Hatchling 1.32.0. The first artifacts are preserved in ignored local build history; they are not the validated distribution. [Hatchling change history](https://hatch.pypa.io/dev/history/hatchling/) explains the default change.
