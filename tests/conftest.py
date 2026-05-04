import sys
import types

try:
    import streamlit  # noqa: F401
except ModuleNotFoundError:
    streamlit_stub = types.ModuleType("streamlit")

    def _noop(*args, **kwargs):
        return None

    streamlit_stub.html = _noop
    streamlit_stub.dataframe = _noop
    streamlit_stub.plotly_chart = _noop
    streamlit_stub.markdown = _noop
    streamlit_stub.caption = _noop
    streamlit_stub.subheader = _noop
    streamlit_stub.info = _noop
    streamlit_stub.error = _noop
    streamlit_stub.write = _noop
    streamlit_stub.download_button = _noop
    streamlit_stub.columns = lambda *args, **kwargs: []
    streamlit_stub.tabs = lambda *args, **kwargs: []
    streamlit_stub.slider = lambda *args, **kwargs: args[2] if len(args) > 2 else None
    streamlit_stub.multiselect = lambda *args, **kwargs: kwargs.get("default", [])
    streamlit_stub.date_input = lambda *args, **kwargs: kwargs.get("value")
    streamlit_stub.sidebar = types.SimpleNamespace(
        markdown=_noop,
        caption=_noop,
        multiselect=lambda *args, **kwargs: kwargs.get("default", []),
        slider=lambda *args, **kwargs: args[2] if len(args) > 2 else None,
        date_input=lambda *args, **kwargs: kwargs.get("value"),
    )
    sys.modules["streamlit"] = streamlit_stub
