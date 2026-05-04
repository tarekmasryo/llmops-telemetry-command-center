import pandas as pd
import plotly.graph_objects as go

from src.charts import baseline_comparison, empty_figure, line_operations


def test_line_operations_returns_plotly_figure() -> None:
    daily = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
            "requests": [10, 12],
            "failure_rate": [0.1, 0.2],
            "sla_breach_rate": [0.05, 0.15],
            "cost_usd": [1.2, 1.6],
        }
    )

    fig = line_operations(daily)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3
    assert fig.layout.title.text == "Daily operating pressure"


def test_empty_figure_returns_annotated_figure() -> None:
    fig = empty_figure("No rows")

    assert isinstance(fig, go.Figure)
    assert fig.layout.annotations[0].text == "No rows"


def test_baseline_comparison_returns_plotly_figure() -> None:
    df = pd.DataFrame(
        {
            "policy": ["review_all", "threshold"],
            "expected_cost": [100.0, 80.0],
            "review_share": [1.0, 0.5],
            "reviewed_rows": [100, 50],
            "precision": [0.2, 0.4],
            "recall": [1.0, 0.8],
        }
    )

    fig = baseline_comparison(df)

    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "Triage baseline comparison"
