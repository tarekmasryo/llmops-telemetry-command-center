from __future__ import annotations

import html
import textwrap
from typing import Any

import pandas as pd
import streamlit as st

CSS = """
<style>
:root{
  --bg:#020617;
  --panel:#0f172a;
  --panel2:#111827;
  --border:rgba(148,163,184,.18);
  --muted:#94a3b8;
  --text:#e5e7eb;
  --blue:#38bdf8;
  --purple:#a78bfa;
  --green:#34d399;
  --amber:#fbbf24;
  --red:#fb7185;
}

html,
body,
[class*="css"]{
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(circle at 20% 0%, rgba(56,189,248,.16), transparent 30%),
    radial-gradient(circle at 80% 0%, rgba(167,139,250,.14), transparent 34%),
    #020617;
}

[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
  border-right: 1px solid var(--border);
}

[data-testid="stHeader"]{
  background: rgba(2,6,23,.78);
  backdrop-filter: blur(16px);
}

.block-container{
  max-width: 1520px;
  padding-top: 4.2rem;
  padding-bottom: 4rem;
}

h1,
h2,
h3{
  letter-spacing: -.04em;
}

hr{
  border-color: rgba(148,163,184,.18);
}

.hero{
  margin-top: .5rem;
  padding: 25px 28px;
  border: 1px solid rgba(148,163,184,.18);
  border-radius: 26px;
  background:
    linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.74)),
    radial-gradient(circle at top right, rgba(56,189,248,.25), transparent 34%);
  box-shadow: 0 24px 80px rgba(0,0,0,.28);
  margin-bottom: 18px;
}

.hero-top{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.hero-kicker{
  color: var(--blue);
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .12em;
  font-weight: 750;
}

.hero-status{
  color: #bbf7d0;
  background: rgba(52,211,153,.10);
  border: 1px solid rgba(52,211,153,.25);
  border-radius: 999px;
  padding: 5px 11px;
  font-size: 11px;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-weight: 700;
}

.hero-title{
  color: #f8fafc;
  font-size: 38px;
  line-height: 1;
  font-weight: 860;
  letter-spacing: -.06em;
  margin: .35rem 0 .55rem;
}

.hero-sub{
  color: #cbd5e1;
  font-size: 15px;
  line-height: 1.6;
  max-width: 980px;
}

.hero-bullets{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.hero-bullet{
  color: #cbd5e1;
  border: 1px solid rgba(148,163,184,.14);
  background: rgba(2,6,23,.26);
  border-radius: 16px;
  padding: 11px 12px;
  font-size: 12px;
  line-height: 1.45;
}

.hero-bullet b{
  color: #f8fafc;
}

.metric-card{
  padding: 16px 17px;
  border: 1px solid rgba(148,163,184,.16);
  border-radius: 21px;
  background: linear-gradient(180deg, rgba(15,23,42,.95), rgba(15,23,42,.72));
  box-shadow: 0 14px 36px rgba(0,0,0,.18);
  min-height: 132px;
}

.metric-label{
  color: var(--muted);
  font-family: "SFMono-Regular", Consolas, monospace;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: .08em;
}

.metric-value{
  color: #f8fafc;
  font-weight: 800;
  font-size: 30px;
  line-height: 1.1;
  margin-top: 9px;
  letter-spacing: -.04em;
}

.metric-help{
  color: #94a3b8;
  font-size: 12px;
  margin-top: 8px;
  line-height: 1.4;
}

.metric-accent{
  width: 44px;
  height: 3px;
  border-radius: 4px;
  margin-top: 12px;
  background: var(--accent, #38bdf8);
}

.alert-card{
  padding: 15px 16px;
  border-radius: 20px;
  border: 1px solid rgba(148,163,184,.16);
  background: rgba(15,23,42,.72);
  margin-bottom: 10px;
}

.alert-critical{
  border-left: 4px solid var(--red);
}

.alert-high{
  border-left: 4px solid #f97316;
}

.alert-medium{
  border-left: 4px solid var(--amber);
}

.alert-ok{
  border-left: 4px solid var(--green);
}

.alert-title{
  color: #f8fafc;
  font-weight: 750;
  font-size: 14px;
  margin-bottom: 5px;
}

.alert-meta{
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}

.badge{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-weight: 700;
}

.badge-red{
  color: #fecaca;
  background: rgba(251,113,133,.13);
  border: 1px solid rgba(251,113,133,.25);
}

.badge-amber{
  color: #fde68a;
  background: rgba(251,191,36,.12);
  border: 1px solid rgba(251,191,36,.25);
}

.badge-green{
  color: #bbf7d0;
  background: rgba(52,211,153,.12);
  border: 1px solid rgba(52,211,153,.25);
}

.badge-blue{
  color: #bae6fd;
  background: rgba(56,189,248,.12);
  border: 1px solid rgba(56,189,248,.25);
}

.section-card{
  padding: 18px;
  border: 1px solid rgba(148,163,184,.15);
  border-radius: 22px;
  background: rgba(15,23,42,.72);
  box-shadow: 0 18px 55px rgba(0,0,0,.18);
  margin-bottom: 10px;
}

.section-title{
  color: #f8fafc;
  font-size: 14px;
  font-weight: 800;
  margin-bottom: 7px;
}

.small-note{
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.58;
}

.kv-grid{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.kv-card{
  padding: 13px 14px;
  border-radius: 18px;
  border: 1px solid rgba(148,163,184,.15);
  background: rgba(15,23,42,.68);
}

.kv-label{
  color: #94a3b8;
  font-size: 10px;
  font-family: "SFMono-Regular", Consolas, monospace;
  text-transform: uppercase;
  letter-spacing: .08em;
}

.kv-value{
  color: #f8fafc;
  font-size: 16px;
  font-weight: 800;
  margin-top: 6px;
  overflow-wrap: anywhere;
}

.code-chip{
  font-family: "SFMono-Regular", Consolas, monospace;
  color: #bae6fd;
  background: rgba(56,189,248,.10);
  border: 1px solid rgba(56,189,248,.20);
  padding: 2px 7px;
  border-radius: 7px;
}

.stTabs [data-baseweb="tab-list"]{
  gap: 8px;
  flex-wrap: wrap;
}

.stTabs [data-baseweb="tab"]{
  border-radius: 999px;
  padding: 8px 16px;
  color: #cbd5e1;
  background: rgba(15,23,42,.55);
  border: 1px solid rgba(148,163,184,.13);
}

.stTabs [aria-selected="true"]{
  background: linear-gradient(135deg, rgba(56,189,248,.24), rgba(167,139,250,.20));
  color: #f8fafc;
  border-color: rgba(56,189,248,.34);
}

[data-testid="stMetric"]{
  background: rgba(15,23,42,.72);
  padding: 14px;
  border-radius: 20px;
  border: 1px solid rgba(148,163,184,.15);
}

[data-testid="stDataFrame"]{
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(148,163,184,.12);
}

@media (max-width: 900px){
  .hero-bullets{
    grid-template-columns: 1fr;
  }

  .kv-grid{
    grid-template-columns: 1fr;
  }
}
</style>
"""


def clean_html(fragment: str) -> str:
    """Return a dedented HTML fragment so Streamlit/Markdown does not render it as code."""
    return textwrap.dedent(fragment).strip()


def render_html(fragment: str) -> None:
    """Render trusted, escaped HTML fragments without Markdown indentation side effects.

    The project pins Streamlit >=1.51, so st.html is available and avoids the
    Markdown parser path that can display indented HTML as raw text.
    """
    st.html(clean_html(fragment))


def install_css() -> None:
    render_html(CSS)


def esc(value: Any) -> str:
    return html.escape(str(value))


def hero(
    title: str,
    subtitle: str,
    bullets: list[tuple[str, str]] | None = None,
    kicker: str = "LLMOps Telemetry Command Center",
    status: str = "Operational dashboard",
) -> None:
    bullet_html = ""
    if bullets:
        bullet_items = "".join(
            f'<div class="hero-bullet"><b>{esc(label)}</b><br>{esc(text)}</div>' for label, text in bullets
        )
        bullet_html = f'<div class="hero-bullets">{bullet_items}</div>'

    render_html(
        f"""
        <div class="hero">
          <div class="hero-top">
            <div class="hero-kicker">{esc(kicker)}</div>
            <div class="hero-status">{esc(status)}</div>
          </div>
          <div class="hero-title">{esc(title)}</div>
          <div class="hero-sub">{esc(subtitle)}</div>
          {bullet_html}
        </div>
        """
    )


def metric_card(label: str, value: str, help_text: str, color: str = "#38bdf8") -> None:
    render_html(
        f"""
        <div class="metric-card" style="--accent:{esc(color)}">
          <div class="metric-label">{esc(label)}</div>
          <div class="metric-value">{esc(value)}</div>
          <div class="metric-help">{esc(help_text)}</div>
          <div class="metric-accent"></div>
        </div>
        """
    )


def badge(text: str, kind: str = "blue") -> str:
    klass = {
        "critical": "badge-red",
        "high": "badge-red",
        "medium": "badge-amber",
        "warn": "badge-amber",
        "watch": "badge-amber",
        "ok": "badge-green",
        "blue": "badge-blue",
    }.get(kind, "badge-blue")
    return f'<span class="badge {klass}">{esc(text)}</span>'


def alert_card(severity: str, title: str, why: str, action: str) -> None:
    sev = severity.lower()
    klass = (
        "alert-ok"
        if sev == "ok"
        else "alert-medium"
        if sev in {"medium", "watch"}
        else "alert-high"
        if sev == "high"
        else "alert-critical"
    )
    render_html(
        f"""
        <div class="alert-card {klass}">
          <div class="alert-title">{badge(severity.upper(), severity)} &nbsp; {esc(title)}</div>
          <div class="alert-meta"><strong>Why:</strong> {esc(why)}<br><strong>Action:</strong> {esc(action)}</div>
        </div>
        """
    )


def artifact_note() -> None:
    render_html(
        """
        <div class="alert-card alert-medium">
          <div class="alert-title">⚠ Artifact scope note</div>
          <div class="alert-meta">Notebook artifacts are computed on the original evaluation window. Sidebar filters update the live dashboard views and simulators, but precomputed artifact verdicts remain the notebook audit trail.</div>
        </div>
        """
    )


def section_card(title: str, body: str) -> None:
    render_html(
        f"""
        <div class="section-card">
          <div class="section-title">{esc(title)}</div>
          <div class="small-note">{esc(body)}</div>
        </div>
        """
    )


def key_value_grid(items: list[tuple[str, str]], columns: int = 2) -> None:
    safe_columns = max(1, min(int(columns), 4))
    cards = []
    for label, value in items:
        cards.append(
            '<div class="kv-card">'
            f'<div class="kv-label">{esc(label)}</div>'
            f'<div class="kv-value">{esc(value)}</div>'
            "</div>"
        )
    style = f"grid-template-columns: repeat({safe_columns}, minmax(0, 1fr));"
    render_html(f'<div class="kv-grid" style="{style}">' + "".join(cards) + "</div>")


def dataframe(df: pd.DataFrame, height: int = 340) -> None:
    st.dataframe(df, hide_index=True, height=height, width="stretch")


def plotly(fig, key: str) -> None:
    """Render a Plotly chart with a stable Streamlit element key.

    Explicit keys prevent duplicate-element collisions when charts have similar
    figure signatures across tabs or reruns.
    """
    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
        config={"displayModeBar": False, "responsive": True},
    )
