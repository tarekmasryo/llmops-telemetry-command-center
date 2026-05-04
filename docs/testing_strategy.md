# Testing Strategy

The test suite is designed to protect the repository from common dashboard failure modes: broken data contracts, invalid artifacts, stale artifact manifests, unsafe rendering regressions, and fragile business logic.

## Current test groups

| Test file | Purpose |
|---|---|
| `tests/test_data.py` | Data readers, type coercion, schema checks, and bundle integrity helpers. |
| `tests/test_metrics.py` | KPI calculations, filtering, risk slices, configured-SLA triage queue behavior, and severity scoring. |
| `tests/test_charts.py` | Plotly figure builders for key dashboard charts and empty-state figures. |
| `tests/test_command_view.py` | Dynamic operations-checklist behavior tied to the routing artifact verdict. |
| `tests/test_policy.py` | Routing simulation and triage threshold lookup behavior. |
| `tests/test_ui.py` | HTML escaping, badge rendering, fragment cleanup, and key-value grid layout behavior. |
| `tests/test_artifact_contracts.py` | Required artifact files, generated-output references, artifact-level schema contracts, and manifest checksum verification. |
| `tests/test_bundle_contract.py` | End-to-end bundle load and cross-table integrity checks. |
| `tests/test_project_quality.py` | Repository hygiene and UI safety guardrails. |

## Local checks

```bash
python scripts/run_tests.py
python -m ruff check app.py src tests scripts
```

## CI checks

GitHub Actions runs the same lint and test checks on push and pull requests to `main`. The Docker job also builds the image, starts the container, and polls Streamlit's `/_stcore/health` endpoint so the published image is not only syntactically buildable but also bootable.

## Future hardening ideas

- Add screenshot smoke tests for critical tabs.
- Add golden-output tests for core KPI tables.
- Add compatibility tests when regenerating artifacts from a newer notebook version.


## CI runtime matrix

The GitHub Actions workflow runs the same Ruff and pytest checks on Python 3.11 and 3.12. This keeps the published compatibility claim tied to an automated check rather than README wording only.


## Deterministic pytest execution

The Makefile and CI run `python scripts/run_tests.py`, which sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` inside Python before invoking pytest. This keeps the release checks focused on the repository's own tests and avoids shell-specific environment-variable syntax on Windows, Linux, and macOS.


## Artifact manifest validation

The bundled `docs/artifact_manifest.md` is checked against the actual release files. The contract test recomputes SHA256 values and validates CSV row and column counts, so artifact changes must be intentional and documented.
