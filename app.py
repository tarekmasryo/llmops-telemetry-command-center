from __future__ import annotations

import streamlit as st

from src.dashboard import DashboardApp
from src.data import load_bundle
from src.ui import install_css

st.set_page_config(
    page_title="LLMOps Telemetry Command Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)
install_css()


@st.cache_data(show_spinner="Loading telemetry bundle...")
def cached_bundle():
    return load_bundle()


def main() -> None:
    try:
        bundle = cached_bundle()
    except Exception as exc:
        st.error(
            "The telemetry bundle could not be loaded. "
            "This app fails fast when required data or artifacts are missing/corrupted."
        )
        st.exception(exc)
        st.stop()
    DashboardApp(bundle).render()


main()
