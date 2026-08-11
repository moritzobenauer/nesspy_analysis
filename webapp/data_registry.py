"""Persisted list of named datasets (run directories) the UI knows about.

Streamlit reruns the whole script on every interaction, so anything not held in
`st.session_state` or on disk is lost between reruns. This module is the on-disk
half: a flat JSON file next to this module, loaded into `st.session_state` once at
app startup and written back on every add/remove so the two never diverge.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(__file__).parent / "datasets.json"


@dataclass
class Dataset:
    name: str
    path: str


def load_registry(path: Path = REGISTRY_PATH) -> list[Dataset]:
    """Load the dataset list from disk. Returns [] if missing or corrupt."""
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not read dataset registry %s: %s", path, e)
        return []
    return [Dataset(name=entry["name"], path=entry["path"]) for entry in raw]


def save_registry(datasets: list[Dataset], path: Path = REGISTRY_PATH) -> None:
    """Write the dataset list to disk atomically (temp file + rename)."""
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps([asdict(d) for d in datasets], indent=2))
    os.replace(tmp_path, path)


def add_dataset(datasets: list[Dataset], name: str, path: str) -> list[Dataset]:
    """Return a new list with `name` added, or raise ValueError if it exists."""
    if any(d.name == name for d in datasets):
        raise ValueError(f"A dataset named '{name}' already exists.")
    return [*datasets, Dataset(name=name, path=path)]


def remove_dataset(datasets: list[Dataset], name: str) -> list[Dataset]:
    """Return a new list with `name` removed. No error if it isn't present."""
    return [d for d in datasets if d.name != name]
