from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_text() -> str:
    paths = [
        ROOT / "app.py",
        *sorted((ROOT / "src").glob("*.py")),
        *sorted((ROOT / "src" / "views").glob("*.py")),
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_app_entrypoint_stays_thin() -> None:
    app_lines = (ROOT / "app.py").read_text(encoding="utf-8").splitlines()
    assert len(app_lines) <= 60
    assert "DashboardApp(bundle).render()" in "\n".join(app_lines)


def test_interface_copy_uses_release_ready_command_center_language() -> None:
    text = source_text().lower()
    expected_terms = [
        "command center",
        "policy lab",
        "triage simulator",
        "review queue",
        "evidence",
        "data explorer",
    ]
    for term in expected_terms:
        assert term in text


def test_custom_html_uses_streamlit_html_renderer() -> None:
    ui_text = (ROOT / "src" / "ui.py").read_text(encoding="utf-8")
    assert "st.html(clean_html(fragment))" in ui_text
    assert "unsafe_allow_html=True" not in ui_text
    assert "st.markdown(clean_html(fragment)" not in ui_text


def test_key_value_grid_does_not_build_indented_html_blocks() -> None:
    ui_text = (ROOT / "src" / "ui.py").read_text(encoding="utf-8")
    start = ui_text.index("def key_value_grid")
    end = ui_text.index("def dataframe", start)
    helper_source = ui_text[start:end]
    assert 'f"""' not in helper_source
    assert '"""' not in helper_source


def test_repository_includes_deployment_and_scope_docs() -> None:
    required = [
        ROOT / "Dockerfile",
        ROOT / ".dockerignore",
        ROOT / "CONTRIBUTING.md",
        ROOT / "DEPLOYMENT.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "artifact_provenance.md",
        ROOT / "docs" / "artifact_manifest.md",
        ROOT / "docs" / "operational_boundaries.md",
        ROOT / "docs" / "testing_strategy.md",
    ]
    for path in required:
        assert path.exists(), f"Missing required release file: {path.relative_to(ROOT)}"


def test_readme_positions_project_as_command_center() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "LLMOps Telemetry Command Center" in readme
    assert "does not contain real customer" in readme
    assert "artifact evidence vs live scenario review" in readme.lower()
    assert "llmops-telemetry-command-center" in readme


def test_plotly_helper_requires_explicit_keys() -> None:
    ui_text = (ROOT / "src" / "ui.py").read_text(encoding="utf-8")
    view_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((ROOT / "src" / "views").glob("*.py"))
    )
    assert "def plotly(fig, key: str)" in ui_text
    assert "st.plotly_chart(" in ui_text
    assert "key=key" in ui_text
    assert "plotly(" in view_text
    assert 'key="' in view_text or 'key=f"' in view_text
    assert "plotly(line_operations(daily))" not in view_text


def test_release_copy_uses_final_command_center_name() -> None:
    release_text = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8"),
            source_text(),
        ]
    )
    assert "LLMOps Telemetry Command Center" in release_text
    assert "llmops-telemetry-command-center" in release_text


def test_readme_states_scope_and_evidence_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "synthetic/offline telemetry" in readme
    assert "artifact evidence vs live scenario review" in readme.lower()
    assert "does not contain real customer" in readme


def test_release_includes_docker_compose_runtime() -> None:
    compose = ROOT / "docker-compose.yml"
    assert compose.exists(), "Missing docker-compose.yml"
    compose_text = compose.read_text(encoding="utf-8")
    assert "llmops-telemetry-command-center" in compose_text
    assert '"8501:8501"' in compose_text


def test_metric_strip_has_single_column_declaration() -> None:
    overview_text = (ROOT / "src" / "views" / "overview.py").read_text(encoding="utf-8")
    start = overview_text.index("def _render_metric_strip")
    metric_strip_source = overview_text[start:]
    assert metric_strip_source.count("st.columns([1.05, 1, 1, 1, 1])") == 1


def test_ci_matrix_matches_public_python_support_claim() -> None:
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'python-version: ["3.11", "3.12"]' in ci_text
    assert "CI-tested on Python `3.11` and `3.12`" in readme


def test_dashboard_is_thin_coordinator_with_view_mixins() -> None:
    dashboard_text = (ROOT / "src" / "dashboard.py").read_text(encoding="utf-8")
    assert "class DashboardApp(" in dashboard_text
    assert "OverviewViewMixin" in dashboard_text
    assert "PolicyLabViewMixin" in dashboard_text
    assert "DataExplorerViewMixin" in dashboard_text
    assert "def _render_command_tab" not in dashboard_text
    assert "def _render_data_explorer_tab" not in dashboard_text
    assert len(dashboard_text.splitlines()) <= 430


def test_view_modules_remain_reviewable() -> None:
    for path in sorted((ROOT / "src" / "views").glob("*.py")):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 320, (
            f"{path.name} is too large for a focused view module"
        )


def test_main_tabs_use_clean_enterprise_labels() -> None:
    dashboard_text = (ROOT / "src" / "dashboard.py").read_text(encoding="utf-8")
    expected_labels = [
        "01 · Command",
        "02 · Hotspots",
        "03 · Policy Lab",
        "04 · Triage Simulator",
        "05 · Review Queue",
        "06 · Evidence",
        "07 · Data Explorer",
    ]
    for label in expected_labels:
        assert label in dashboard_text
    dashboard_labels = [line for line in dashboard_text.splitlines() if "01 ·" in line or "02 ·" in line]
    assert dashboard_labels


def test_data_explorer_search_uses_literal_matching() -> None:
    explorer_text = (ROOT / "src" / "views" / "data_explorer.py").read_text(encoding="utf-8")
    assert "str.contains(search.lower(), na=False, regex=False)" in explorer_text


def test_evidence_view_reads_current_triage_policy_schema() -> None:
    evidence_text = (ROOT / "src" / "views" / "evidence.py").read_text(encoding="utf-8")
    assert 'payload.get("metrics", {})' in evidence_text
    assert 'payload.get("selected_policy_metrics", {})' in evidence_text
    assert 'payload.get("model", {})' not in evidence_text
    assert 'payload.get("selected_operating_point", {})' not in evidence_text


def test_ci_includes_format_and_docker_smoke_gates() -> None:
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python -m ruff format --check app.py src tests scripts" in ci_text
    assert "docker-build:" in ci_text
    assert "python scripts/docker_smoke_test.py --image llmops-telemetry-command-center:ci --build" in ci_text


def test_make_check_matches_ci_quality_gates() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "format-check:" in makefile
    assert "$(PYTHON) -m ruff format --check app.py src tests scripts" in makefile
    assert "check: lint format-check compile test" in makefile
    assert "$(PYTHON) scripts/run_tests.py" in makefile


def test_triage_queue_uses_configured_sla_parameter() -> None:
    metrics_text = (ROOT / "src" / "metrics.py").read_text(encoding="utf-8")
    triage_start = metrics_text.index("def build_triage_queue")
    triage_source = metrics_text[triage_start:]
    assert "sla_ms: int = 2200" in triage_source
    assert 'q["latency_ms"] >= sla_ms' in triage_source
    assert "/ 2200" not in triage_source


def test_cross_platform_test_runner_sets_pytest_plugin_guard() -> None:
    runner = (ROOT / "scripts" / "run_tests.py").read_text(encoding="utf-8")
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in runner
    assert "subprocess.call" in runner
    assert "sys.executable" in runner


def test_dockerfile_healthcheck_is_single_instruction() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    healthcheck_source = dockerfile[
        dockerfile.index("HEALTHCHECK") : dockerfile.index("CMD [", dockerfile.index("HEALTHCHECK"))
    ]
    assert "<<" not in healthcheck_source
    assert "python -c" in healthcheck_source
    assert "_stcore/health" in healthcheck_source


def test_docker_smoke_runner_is_release_gate() -> None:
    runner = (ROOT / "scripts" / "docker_smoke_test.py").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "docker" in runner
    assert "build" in runner
    assert "run" in runner
    assert "_stcore/health" in runner
    assert "docker-check: docker-smoke" in makefile
