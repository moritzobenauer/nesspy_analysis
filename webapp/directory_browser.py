"""A standalone, in-app directory browser widget (compact, scrollable).

No native OS dialog and no tkinter -- browsers can't open one on a served page,
and even for a locally-run Streamlit app, sys.path/tkinter setups tend to be
finicky on macOS. This is pure Streamlit.

Layout (deliberately kept to a fixed, small vertical footprint):

    [⬆ Up] [ path text box ] [✅ Use this folder]
    [ filter box, only when the folder has many children ]
    ┌ fixed-height scroll box ────────────────────────────┐
    │ 📁 subfolder-name                              [＋] │
    └─────────────────────────────────────────────────────┘

The scroll box means a directory with 300 children costs the same screen space
as one with three. The `＋` button appears only next to folders that already
look like run directories, so a run directory can be picked *without* first
navigating into it -- that is the common case and it is now one click.

Navigation and selection are done via `on_click` callbacks, not by writing to a
widget's session_state key mid-script: Streamlit forbids setting a widget's own
key after that widget has already been instantiated in the current run, which a
straight-line "handle click, then write state, then st.rerun()" version hits as
soon as a button below the text input tries to update it. Callbacks run *before*
the next script run starts, so they can freely set any key.

Kept free of any other `webapp` import so it stays a reusable, drop-in component.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

# Above this many subdirectories a filter box is shown; below it, it would just
# be noise.
FILTER_THRESHOLD = 8


def _looks_like_run_dir(path: Path) -> bool:
    """Cheap one-level-down check: does any subdirectory hold an out.csv?

    A badge/hint for the browser UI, not full validation -- mirrors the same
    check in webapp/pipeline_status.py's RunStatus.looks_like_run_dir, but
    reimplemented here (not imported) to keep this module standalone.
    """
    try:
        for child in path.iterdir():
            if child.is_dir() and (child / "out.csv").is_file():
                return True
    except (PermissionError, OSError):
        return False
    return False


def _subdirectories(path: Path) -> list[Path]:
    """Sorted subdirectories of `path`; warns and returns [] if unreadable."""
    try:
        return sorted(
            (p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")),
            key=lambda p: p.name.lower(),
        )
    except PermissionError:
        st.warning(f"Permission denied listing {path}.")
    except OSError as e:
        st.warning(f"Could not list {path}: {e}")
    return []


def directory_browser(
    key: str,
    initial_root: str | Path = Path.home(),
    *,
    list_height: int = 260,
) -> Path | None:
    """Render the browser; returns a Path only on the rerun a folder was picked
    (either via "Use this folder" or a row's ＋ button), and None otherwise.
    """
    current_path_key = f"{key}__current_path"
    path_input_key = f"{key}__path_input"
    selection_key = f"{key}__selection"
    filter_key = f"{key}__filter"
    error_key = f"{key}__error"

    if current_path_key not in st.session_state:
        st.session_state[current_path_key] = str(initial_root)
        st.session_state[path_input_key] = str(initial_root)

    # Checked first: this is what makes "returns non-None only on its own
    # rerun" work -- the pending selection is consumed immediately, before any
    # widgets (whose own callbacks might set it again) are rendered.
    if st.session_state.get(selection_key):
        picked = st.session_state[selection_key]
        st.session_state[selection_key] = None
        return Path(picked)

    def _go(new_path: Path) -> None:
        st.session_state[current_path_key] = str(new_path)
        st.session_state[path_input_key] = str(new_path)
        st.session_state[filter_key] = ""  # a new folder starts unfiltered

    def _select(path: Path) -> None:
        st.session_state[selection_key] = str(path)

    def _on_path_typed() -> None:
        candidate = Path(st.session_state[path_input_key]).expanduser()
        if candidate.is_dir():
            st.session_state[current_path_key] = str(candidate)
            st.session_state[filter_key] = ""
        else:
            st.session_state[error_key] = f"{candidate} is not a directory."

    current_path = Path(st.session_state[current_path_key])

    # --- one-line toolbar: up / path / select ------------------------------
    col_up, col_path, col_select = st.columns([1, 6, 3], vertical_alignment="bottom")
    col_up.button(
        "⬆",
        key=f"{key}__up",
        on_click=_go,
        args=(current_path.parent,),
        help=f"Up to {current_path.parent}",
        width="stretch",
    )
    col_path.text_input(
        "Path",
        key=path_input_key,
        on_change=_on_path_typed,
        label_visibility="collapsed",
    )
    col_select.button(
        "✅ Use this folder",
        key=f"{key}__select",
        on_click=_select,
        args=(current_path,),
        width="stretch",
    )

    if st.session_state.get(error_key):
        st.error(st.session_state[error_key])
        st.session_state[error_key] = None

    subdirs = _subdirectories(current_path)

    # --- optional filter box, only worth the space in large directories ----
    if len(subdirs) > FILTER_THRESHOLD:
        needle = st.text_input(
            "Filter",
            key=filter_key,
            placeholder=f"filter {len(subdirs)} folders…",
            label_visibility="collapsed",
        ).strip().lower()
        if needle:
            subdirs = [p for p in subdirs if needle in p.name.lower()]

    # --- fixed-height scroll box, one row per folder -----------------------
    with st.container(height=list_height, border=True):
        if not subdirs:
            st.caption("No subfolders here.")
        for subdir in subdirs:
            is_run_dir = _looks_like_run_dir(subdir)
            col_nav, col_add = st.columns([9, 1], vertical_alignment="center")
            col_nav.button(
                f"{'📊' if is_run_dir else '📁'} {subdir.name}",
                key=f"{key}__nav__{subdir.name}",
                on_click=_go,
                args=(subdir,),
                width="stretch",
            )
            # Only run directories get the shortcut: everything else has to be
            # opened first, which is also the honest signal that there is
            # nothing to add here.
            if is_run_dir:
                col_add.button(
                    "＋",
                    key=f"{key}__pick__{subdir.name}",
                    on_click=_select,
                    args=(subdir,),
                    help=f"Select {subdir.name} without opening it",
                    width="stretch",
                )

    return None
