"""Filesystem discovery of out.csv and lattice_final.npy files."""
import numpy as np
import pytest

from nesspy_analysis import iterdirs, find_all_final_configs


def test_iterdirs_finds_out_csv_recursively(tmp_path):
    (tmp_path / "run_a").mkdir()
    (tmp_path / "run_b" / "seed0").mkdir(parents=True)
    (tmp_path / "run_a" / "out.csv").write_text("x\n")
    (tmp_path / "run_b" / "seed0" / "out.csv").write_text("x\n")

    files, count = iterdirs(tmp_path)
    assert count == 2
    assert {f.name for f in files} == {"out.csv"}


def test_find_all_final_configs(tmp_path):
    (tmp_path / "mu1").mkdir()
    np.save(tmp_path / "mu1" / "lattice_final.npy", np.zeros((2, 2)))
    found = find_all_final_configs(tmp_path)
    assert len(found) == 1 and found[0].name == "lattice_final.npy"


def test_missing_path_raises(tmp_path):
    with pytest.raises(ValueError):
        iterdirs(tmp_path / "does_not_exist")


def test_no_matches_raises(tmp_path):
    with pytest.raises(ValueError):
        iterdirs(tmp_path)              # empty dir, no out.csv
    with pytest.raises(ValueError):
        find_all_final_configs(tmp_path)
