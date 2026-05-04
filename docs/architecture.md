# Architecture

## Purpose

LLMOps Telemetry Command Center is a Streamlit operations interface over bundled synthetic LLM telemetry and notebook-generated evaluation artifacts. It turns reliability, latency, cost, routing, drift, and review-triage signals into a decision-ready workflow for technical review.

The application is intentionally structured as a layered dashboard system rather than a single script of charts.

---

## System flow

```text
Telemetry CSVs + evaluation artifacts
        |
        v
src.data.load_bundle()
        |
        |-- required file checks
        |-- schema validation
        |-- type normalization
        |-- JSON artifact contract checks
        |-- cross-table integrity checks
        v
DataBundle
        |
        +--> src.metrics
        |       KPIs, incident board, hotspots, risk slices,
        |       review queues, cohorts, and instruction diagnostics
        |
        +--> src.policy
        |       routing scenario review and triage threshold lookup
        |
        +--> src.charts
        |       Plotly figure builders with stable chart semantics
        |
        +--> src.dashboard
        |       thin Streamlit coordinator, sidebar state, and tab routing
        |
        +--> src.views
        |       focused tab-level view mixins for command, hotspots,
        |       policy lab, triage, evidence, and data exploration
        |
        +--> src.ui
                reusable UI primitives, safe HTML helpers,
                tables, cards, and Plotly rendering wrappers
```

---

## Layer responsibilities

| Layer | Responsibility | Explicitly avoids |
|---|---|---|
| `app.py` | Streamlit page setup, CSS install, bundle loading, top-level error handling | Domain logic and chart construction |
| `src.data` | File loading, schema checks, type coercion, artifact validation, cross-table integrity | UI decisions and policy interpretation |
| `src.metrics` | KPIs, hotspots, incident board, cohorts, risk slices, review queue preparation | Streamlit rendering |
| `src.policy` | Routing scenario review and triage threshold calculations | Overriding held-out artifact verdicts |
| `src.charts` | Plotly figures with consistent layout conventions | Data loading or mutation |
| `src.ui` | Cards, tables, safe HTML rendering, Plotly wrapper with explicit keys | Business rules |
| `src.models` | Immutable dataclasses for sidebar settings and held-out routing verdicts | Rendering or file I/O |
| `src.dashboard` | Thin workflow coordinator, sidebar state, and tab routing | Tab-specific rendering details |
| `src.views.*` | Focused view mixins for each dashboard surface | Data loading, validation, or artifact mutation |
| `tests/` | Contract, metric, policy, UI guardrail, and project-quality checks | Runtime UI rendering |

---


## Code organization pattern

The Streamlit layer uses a small coordinator plus focused view mixins. This keeps the app easy to review without introducing a heavy framework:

```text
DashboardApp
  ├── builds sidebar settings and filtered state
  ├── computes shared KPIs and held-out routing truth
  └── composes view mixins
        ├── OverviewViewMixin
        ├── CommandViewMixin
        ├── HotspotsViewMixin
        ├── PolicyLabViewMixin
        ├── TriageViewMixin
        ├── EvidenceViewMixin
        └── DataExplorerViewMixin
```

This is intentionally modest OOP: composition through mixins, immutable settings via dataclasses, and pure helper modules for metrics/policy/chart generation. It avoids a large inheritance hierarchy while removing the previous single-controller pressure from the dashboard layer.

---

## Data model

The app expects two classes of inputs.

### 1. Telemetry tables

| Table | Role |
|---|---|
| `llm_system_interactions.csv` | Request-level operational telemetry |
| `llm_system_sessions_summary.csv` | Session-level operational aggregates |
| `llm_system_users_summary.csv` | Synthetic account/user-level summaries |
| `llm_system_prompts_lookup.csv` | Prompt/template metadata |
| `llm_system_instruction_tuning_samples.csv` | Instruction-template examples |

### 2. Evaluation artifacts

| Artifact | Role |
|---|---|
| `decision_artifact.json` | Structured decision and quality artifact |
| `routing_backtest_summary.csv` | Held-out routing policy result |
| `routing_policy_use_case.csv` | Use-case-level routing evidence |
| `drift_report.csv` | Drift-signal summary |
| `triage_threshold_policy.json` | Offline triage policy metadata |
| `triage_threshold_curve.csv` | Threshold/cost/review-load trade-off curve |
| `triage_baseline_comparison.csv` | Baseline comparison for triage strategies |
| `triage_actions_preview.csv` | Review-queue preview artifact |

---

## Startup validation

The app fails fast when evidence is missing or structurally invalid. This is deliberate.

Startup checks include:

- required CSV and JSON artifact existence;
- non-empty tables;
- required columns;
- numeric type coercion for latency, cost, scores, and rates;
- timestamp normalization;
- JSON keys required by the decision artifact;
- cross-table references between interactions, sessions, users, prompts, and artifacts;
- negative-value guards for core operational fields.

A clean interface with broken evidence is more dangerous than a loud startup failure.

---

## Artifact evidence vs live scenario review

The app separates operational exploration from held-out evaluation evidence.

### Held-out artifacts

Notebook-generated artifacts are treated as audit evidence. Examples:

- routing backtest verdicts;
- triage threshold policy;
- drift report;
- structured decision artifact.

These artifacts do not change when the user applies sidebar filters.

### Live scenario review views

The dashboard also provides live views based on the active filters and operator knobs:

- filtered KPI strip;
- live risk slices;
- routing scenario assumptions;
- review queue subset;
- data explorer tables.

These views support investigation but do not overwrite artifact verdicts.

---

## Dashboard workflow

```text
Command
  -> What is the current operating state?

Hotspots
  -> Which provider/model/use-case slices drive pressure?

Policy Lab
  -> What did the held-out routing artifact conclude?
  -> What does the filtered scenario review suggest?

Triage Simulator
  -> How does threshold choice affect review load, cost, precision, and recall?

Review Queue
  -> Which rows should be inspected first?

Evidence
  -> What artifacts support the decision?

Data Explorer
  -> What raw or cohort-level evidence needs deeper inspection?
```

---

## UI safety decisions

The UI layer follows a few strict rules:

- custom HTML is rendered through controlled helpers;
- text inserted into HTML is escaped;
- Plotly charts require explicit Streamlit keys;
- raw JSON appears inside expanders, not as default page content;
- chart titles and labels use operator-readable text, not internal column names where possible;
- unsupported states are surfaced through info/warning cards instead of silent empty charts.

---

## Testing strategy

The test suite covers:

- data bundle loading;
- schema and artifact contracts;
- JSON artifact shape;
- cross-table integrity assumptions;
- metric calculations;
- routing and triage policy helpers;
- Streamlit UI guardrails;
- documentation and release file presence;
- public copy guardrails to avoid low-signal release wording.

CI runs Ruff and pytest on Python `3.11` and `3.12`.

---

## Deployment shape

The repository supports three runtime modes:

1. **Local Streamlit** for development and review.
2. **Docker / Docker Compose** for reproducible local execution.
3. **Hosted Streamlit runtime** such as Streamlit Community Cloud or Hugging Face Spaces.

The included data is bundled for a frictionless first run. A larger operational deployment would externalize telemetry storage, artifact refresh jobs, secrets management, authentication, and monitoring.

---

## Extension points

Good next engineering extensions include:

- scheduled artifact refresh from a notebook or batch job;
- database-backed telemetry storage;
- authenticated internal deployment;
- alert channels for SLA/failure/cost thresholds;
- richer provider/model comparison windows;
- generated Markdown incident brief exports;
- CI validation for artifact regeneration.
