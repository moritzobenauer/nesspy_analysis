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
