# Changelog

## 1.0.0 - 2026-05-03

Official GitHub release for **LLMOps Telemetry Command Center**.

### Added

- Streamlit command-center interface for LLM telemetry review.
- Synthetic telemetry bundle and notebook-generated evaluation artifacts.
- KPI strip for reliability, latency, cost, failure pressure, and health score.
- Hotspot analysis by provider, model, use case, and operational pressure.
- Routing policy lab with held-out artifact separation and live scenario review views.
- Triage threshold simulator with cost, review share, precision, recall, and confusion-matrix context.
- Filter-aware review queue and evidence browser.
- Dockerfile, Docker Compose, Makefile, CI, deployment guide, and architecture documentation.
- Test suite for data contracts, artifact contracts, metrics, policy helpers, UI guardrails, and release quality.
- Focused Streamlit view modules with a thin dashboard coordinator and typed settings models.

### Hardened

- Explicit Plotly chart keys to prevent duplicate Streamlit element IDs.
- Controlled HTML rendering helpers to avoid raw HTML appearing in the interface.
- Public-facing copy aligned around operations, evidence, and review workflows.
- Split the previous monolithic dashboard controller into focused view mixins for cleaner review and maintenance.
- Cache and build artifacts excluded from the release package.
- Release preview screenshot refreshed to match the final Triage Simulator tab label.
- Artifact provenance documentation updated to reflect prompt and instruction-sample integrity checks.
- Drift report severity labels made explicit for cleaner evidence visualization.
- Evidence browser aligned with the current triage policy artifact schema.
- Main dashboard tab labels cleaned for a more enterprise-oriented interface.
- Artifact manifest checksums now covered by an automated contract test.
- Docker image build added to CI release checks.
- Ruff format check added to CI and local `make check`.
- Data Explorer search now treats user input as literal text to avoid regex parsing failures.
- Release-quality tests now focus on positive public-facing guarantees and runtime safety checks.
- Dashboard settings filters now use immutable tuples to match the frozen settings model.
- Review-queue priority and reason labels now use the configured SLA target instead of a fixed latency threshold.
- Operations checklist now follows the loaded routing artifact verdict instead of a fixed rollout recommendation.
- `is_failure` validation now rejects invalid required boolean values before metrics are computed.
- UI helper and chart-builder tests added for behavior-level coverage.
- Scoring heuristics documented in code as operator-review signals rather than calibrated rollout models.
- `CONTRIBUTING.md` added with local validation and synthetic-data contribution boundaries.
- `make check` now uses a cross-platform Python test runner for consistent Windows, Linux, and macOS validation.

- Docker healthcheck rewritten as a single valid Dockerfile instruction.
- Docker CI now performs a container smoke test against Streamlit's health endpoint after building the image.
- Added `scripts/docker_smoke_test.py` and `make docker-check` for production-style container validation.

