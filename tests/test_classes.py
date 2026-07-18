"""Dataclasses, bond-counting internals, and the cluster-observable worker."""
import dataclasses

import numpy as np
import pytest

from nesspy_analysis import Thermos, Lattice2D
from nesspy_analysis.classes import (
    _get_nns, _count_lattice_pairs, _process_cluster_observables_file,
    get_steady_state_probabilities_numerical,
)


def test_thermos_defaults_and_frozen():
    t = Thermos()
    assert (t.jhom, t.jhet, t.method) == (-3.5, -2.0, "NODRIVE")
    assert t.epsilon_matrix.shape == (2, 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.jhom = 0.0


def test_lattice2d_volume():
    assert Lattice2D(x_size=100, y_size=80).volume == 8000


def test_get_nns_counts_bonds_under_pbc():
    # Uniform blue lattice: every neighbour of the centre site is a 2-2 bond.
    lat = np.full((3, 3), 2)
    assert _get_nns(lat, x=1, y=1) == (0, 4, 0)  # (p11, p22, p12)
    # A lone red site among blues -> four 1-2 bonds, no like-bonds.
    lat[1, 1] = 1
    assert _get_nns(lat, x=1, y=1) == (0, 0, 4)


def test_count_lattice_pairs_uniform():
    # Fully-blue HxW torus: 4 same-type bonds per site (each bond seen twice).
    lat = np.full((4, 5), 2)
    p11, p22, p12, n_ones, n_twos = _count_lattice_pairs(lat)
    assert (p11, p12, n_ones) == (0, 0, 0)
    assert p22 == 4 * 4 * 5
    assert n_twos == 4 * 5


def test_worker_uniform_blue_gives_zero_q_full_r(tmp_path):
    # All-blue crop: no wrong bonds (q=0) and one cluster filling the crop (r=1).
    f = tmp_path / "lattice_final.npy"
    np.save(f, np.full((10, 10), 2))
    mu, q, r = _process_cluster_observables_file((0.5, f, 0.2, 0.7, 8))
    assert mu == 0.5
    assert q == pytest.approx(0.0)
    assert r == pytest.approx(1.0)


def test_worker_checkerboard_all_wrong_bonds_no_clusters(tmp_path, checkerboard):
    # Checkerboard: every bond is 1-2 (q=1) and blue sites are isolated (r=0).
    # Use the full even-width lattice so PBC wraps the checkerboard consistently
    # (an odd-width crop would create spurious like-bonds at the seam).
    f = tmp_path / "lattice_final.npy"
    np.save(f, checkerboard)
    _, q, r = _process_cluster_observables_file((0.0, f, 0.0, 1.0, 8))
    assert q == pytest.approx(1.0)
    assert r == pytest.approx(0.0)


def test_steady_state_probabilities_normalised():
    # The two returned occupancies partition the 5-state stationary vector.
    p_active, p_non_bonding = get_steady_state_probabilities_numerical(
        epsilon_homo=-3.5, epsilon_hetero=-2.0, mu=1.0,
        F=np.exp(-2.0), M=1.0, k=1.0, environment=(1, 1), scheme="HOMO",
    )
    assert p_active + p_non_bonding == pytest.approx(1.0)
    assert 0.0 <= p_active <= 1.0 and 0.0 <= p_non_bonding <= 1.0
