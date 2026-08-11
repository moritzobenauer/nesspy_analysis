"""Tab 1: browse to a run directory, verify it's been analyzed, name it, add it.

Layout is two columns -- browser on the left, the "picked folder" panel on the
right -- so picking and adding are visible at the same time without scrolling.
Picking a folder pre-fills the name box with the folder's own name (made unique
if needed), so the usual path is: click ＋ next to a 📊 folder, click Add.

Adding/removing a dataset happens inside `on_click` callbacks (not inline after
the widgets are declared): Streamlit forbids writing to a widget's own
session_state key once that widget has already been instantiated in the current
script run, which an inline "click add, then clear the name box" hits directly.
Callbacks run before the next rerun starts, so they can freely reset widget state.
"""

from pathlib import Path

import streamlit as st

from webapp.data_registry import add_dataset, remove_dataset, save_registry
from webapp.directory_browser import directory_browser
from webapp.pipeline_status import RunStatus, compute_run_status, is_analyzed

ADD_ERROR_KEY = "load_tab__add_error"
NAME_KEY = "load_tab__name_input"
PENDING_KEY = "load_tab__pending_path"


def _unique_name(base: str) -> str:
    """`base`, or `base-2`, `base-3`, ... if that name is already taken."""
    taken = {d.name for d in st.session_state["datasets"]}
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def _add_clicked() -> None:
    name = st.session_state.get(NAME_KEY, "").strip()
    pending_path = st.session_state.get(PENDING_KEY)
    if not name or not pending_path:
        return
    try:
        st.session_state["datasets"] = add_dataset(
            st.session_state["datasets"], name, pending_path
        )
        save_registry(st.session_state["datasets"])
        st.session_state[PENDING_KEY] = None
        st.session_state[NAME_KEY] = ""
        st.session_state[ADD_ERROR_KEY] = None
    except ValueError as e:
        st.session_state[ADD_ERROR_KEY] = str(e)


def _remove_clicked(name: str) -> None:
    st.session_state["datasets"] = remove_dataset(st.session_state["datasets"], name)
    save_registry(st.session_state["datasets"])


def _status_badges(status: RunStatus) -> str:
    """One compact markdown line of green/red badges, replacing four st.metrics."""
    checks = [
        ("run dir", status.looks_like_run_dir),
        ("analysis CSV", status.has_analysis_csv),
        ("up to date", status.has_analysis_csv and not status.analysis_stale),
        ("lattices plotted", status.has_lattice_overview),
    ]
    return " ".join(
        f":{'green' if ok else 'red'}-badge[{'✔' if ok else '✘'} {label}]"
        for label, ok in checks
    )


def render_load_data_tab() -> None:
    col_browse, col_pick = st.columns([3, 2], gap="medium")

    with col_browse:
        st.markdown("**Browse**")
        st.caption(
            "📊 = folder that already looks like a run directory (one subfolder "
            "per chemical potential, each with an out.csv); 📁 = plain folder. "
            "Click a name to open it, ＋ to pick it without opening."
        )
        selected = directory_browser(key="load_tab", initial_root=Path.home())
        if selected is not None:
            st.session_state[PENDING_KEY] = str(selected)
            # Safe to write the name widget's key here: the widget itself is
            # only instantiated further down in this same script run.
            st.session_state[NAME_KEY] = _unique_name(selected.name)
            st.session_state[ADD_ERROR_KEY] = None

    with col_pick:
        st.markdown("**Add to the analysis list**")
        pending_path = st.session_state.get(PENDING_KEY)

        status = None
        if not pending_path:
            st.caption("No folder picked yet.")
        else:
            st.code(pending_path, language=None, wrap_lines=True)
            status = compute_run_status(Path(pending_path))
            st.markdown(_status_badges(status))

            if status.has_failed_marker and not status.failed_marker_stale:
                st.error(
                    "This run's analysis previously failed (analysis_failed.md "
                    "is present). See that file in the run directory."
                )

            if not is_analyzed(status):
                st.warning(
                    "Not analyzed yet (or new out.csv data since the last "
                    "analysis). Run `2026/analyzing_order_disorder.py` or "
                    "`database/run_pipeline.sh` on it first -- this viewer "
                    "never runs the analysis itself."
                )

        gate_ok = status is not None and is_analyzed(status)
        col_name, col_add = st.columns([3, 1], vertical_alignment="bottom")
        name = col_name.text_input(
            "Dataset name",
            key=NAME_KEY,
            disabled=not gate_ok,
            label_visibility="collapsed",
            placeholder="dataset name",
        )
        col_add.button(
            "Add",
            key="load_tab__add_btn",
            disabled=not gate_ok or not name.strip(),
            on_click=_add_clicked,
            type="primary",
            width="stretch",
        )
        if st.session_state.get(ADD_ERROR_KEY):
            st.error(st.session_state[ADD_ERROR_KEY])

    st.divider()
    st.markdown(f"**Loaded datasets** ({len(st.session_state['datasets'])})")
    datasets = st.session_state["datasets"]
    if not datasets:
        st.caption("None yet.")
        return

    for d in datasets:
        col_name, col_path, col_del = st.columns(
            [2, 6, 1], vertical_alignment="center"
        )
        col_name.write(d.name)
        col_path.caption(f"`{d.path}`")
        col_del.button(
            "🗑",
            key=f"remove__{d.name}",
            on_click=_remove_clicked,
            args=(d.name,),
            help=f"Remove {d.name} from the list (does not touch the data)",
        )
