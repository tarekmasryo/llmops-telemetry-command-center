# Contributing

Thanks for considering an improvement to LLMOps Telemetry Command Center.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

## Local validation

Run the same checks used by CI before opening a pull request:

```bash
python -m ruff check app.py src tests scripts
python -m ruff format --check app.py src tests scripts
python -m compileall app.py src tests scripts
python scripts/run_tests.py
```

## Change expectations

- Keep the dashboard self-contained and reproducible with the bundled synthetic telemetry.
- Preserve the boundary between held-out artifacts and live scenario review.
- Add or update tests when changing validation, metrics, policy logic, UI helpers, or chart builders.
- Keep public documentation focused on operational behavior, evidence boundaries, and reproducible usage.

## Data and artifacts

The bundled data is synthetic/offline telemetry. Do not add real customer data, credentials, billing records, incident reports, or sensitive user information.
