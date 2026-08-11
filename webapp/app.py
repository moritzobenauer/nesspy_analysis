"""Streamlit viewer for nesspy_analysis simulation data.

Run with: uv run streamlit run webapp/app.py (from any directory).

Strictly read-only over the existing database/ pipeline -- this app never
triggers analysis itself, only displays what has already been cached to disk.
"""

import sys
from pathlib import Path

# Streamlit's script runner doesn't reliably put the repo root (this file's
# parent's parent) on sys.path -- it depends on the cwd the command was
# launched from. Add it explicitly so `from webapp....` imports below (and the
# ones inside webapp/tabs/*.py) resolve regardless of launch directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from webapp.data_registry import load_registry
from webapp.tabs.tab_compare import render_compare_tab
from webapp.tabs.tab_load_data import render_load_data_tab
from webapp.tabs.tab_overview import render_overview_tab

st.set_page_config(page_title="nesspy_analysis viewer", layout="wide")

# A gradient cannot be expressed in .streamlit/config.toml (it only takes flat
# colours), so it is injected as CSS here. Two layers: a diagonal deep-navy ->
# slate-grey ramp, plus a soft blue glow in the top-left corner that keeps the
# dark end from looking like a flat block. `background-attachment: fixed`
# anchors both to the viewport, so a long tab scrolls over the gradient instead
# of dragging it along (and short tabs still show the full ramp).
#
# The rule is applied to every layer Streamlit stacks between <body> and the
# page content, with the inner ones forced transparent: the theme paints a flat
# `backgroundColor` on some of them depending on version, which would otherwise
# cover the gradient completely.
GRADIENT = (
    "radial-gradient(1200px 800px at 8% -10%, rgba(70,130,255,0.22), transparent 62%), "
    "linear-gradient(135deg, #070c18 0%, #111c33 32%, #232c42 62%, #414a5e 100%)"
)
BACKGROUND_CSS = f"""
<style>
.stApp {{
    background-image: {GRADIENT};
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-size: cover;
}}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stBottom"],
section.main,
header[data-testid="stHeader"] {{
    background: transparent !important;
}}
</style>
"""
# The gradient only makes sense against the dark theme in
# .streamlit/config.toml, and Streamlit reads that file from the *current
# working directory* only. Launched from somewhere else it falls back to
# whatever theme the browser asks for, so painting the dark gradient anyway
# could put dark text on a dark page. Paint it only when the dark theme is
# actually in force, and say why when it isn't. NOTE: config.toml is read once
# at server start -- editing it needs a restart, not just a rerun.
if st.get_option("theme.base") == "dark":
    st.markdown(BACKGROUND_CSS, unsafe_allow_html=True)
else:
    st.warning(
        "Start this app from the repository root (`uv run streamlit run "
        "webapp/app.py`) so `.streamlit/config.toml` is picked up -- without "
        "its dark theme the gradient background is skipped."
    )

if "datasets" not in st.session_state:
    st.session_state["datasets"] = load_registry()

st.title("nesspy_analysis — simulation viewer")
st.caption(f"{len(st.session_state['datasets'])} dataset(s) loaded")

tab_load, tab_overview, tab_compare = st.tabs(["Load data", "Overview", "Compare"])
with tab_load:
    render_load_data_tab()
with tab_overview:
    render_overview_tab()
with tab_compare:
    render_compare_tab()
