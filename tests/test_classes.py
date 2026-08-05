"""Dataclasses, bond-counting internals, and the cluster-observable worker."""
import dataclasses

import numpy as np
import pytest

from nesspy_analysis import Thermos, Lattice2D
from nesspy_analysis.classes import (
    _get_nns, _count_lattice_pairs, _process_cluster_observables_file,
    get_steady_state_probabilities_numerical, scheme_rescaled_drive_and_rate,
    scheme_from_hrc, scheme_short_label, scheme_math_label,
)


# A square lattice has four nearest neighbours, so n_red + n_blue <= 4.
MAX_NEIGHBOURS = 4


def _drives(scheme, dmu0, environments):
    """Effective (dmu_red, dmu_blue) per environment for a scheme."""
    M = np.exp(dmu0)
    out = []
    for env in environments:
        M_red, M_blue, _ = scheme_rescaled_drive_and_rate(scheme, M=M, k=1.0,
                                                          environment=env)
        out.append((np.log(M_red), np.log(M_blue)))
    return out


def test_thermos_defaults_and_frozen():
    t = Thermos()
    assert (t.jhom, t.jhet, t.method) == (-3.5, -2.0, "S0")
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
        F=np.exp(-2.0), M=1.0, k=1.0, environment=(1, 1), scheme="S1",
    )
    assert p_active + p_non_bonding == pytest.approx(1.0)
    assert 0.0 <= p_active <= 1.0 and 0.0 <= p_non_bonding <= 1.0


@pytest.mark.parametrize(
    "scheme", ["S1", "S2", "S3", "S4", "S5", "S6"]
)
def test_steady_state_probabilities_all_schemes_normalised(scheme):
    # Every registered driving scheme must return a valid probability partition
    # for an asymmetric environment (so S6's red/blue split is exercised).
    p_active, p_non_bonding = get_steady_state_probabilities_numerical(
        epsilon_homo=-3.5, epsilon_hetero=-2.0, mu=1.0,
        F=np.exp(-2.0), M=np.exp(0.5), k=1.0, environment=(2, 0), scheme=scheme,
    )
    assert p_active + p_non_bonding == pytest.approx(1.0)
    assert 0.0 <= p_active <= 1.0 and 0.0 <= p_non_bonding <= 1.0


def test_steady_state_probabilities_unknown_scheme_raises():
    with pytest.raises(ValueError):
        get_steady_state_probabilities_numerical(
            epsilon_homo=-3.5, epsilon_hetero=-2.0, mu=1.0,
            F=np.exp(-2.0), M=1.0, k=1.0, environment=(1, 1), scheme="NOPE",
        )


def test_scheme6_red_blue_drives_differ():
    # S6 conditions the drive on colour, so an asymmetric environment must break
    # the symmetry between the red-active and blue-active occupancies that a
    # symmetric scheme (e.g. S5) preserves at these equal couplings.
    kwargs = dict(
        epsilon_homo=-3.5, epsilon_hetero=-3.5, mu=1.0,
        F=np.exp(-1.0), M=np.exp(1.0), k=1.0, environment=(2, 0),
    )
    p6, _ = get_steady_state_probabilities_numerical(scheme="S6", **kwargs)
    p5, _ = get_steady_state_probabilities_numerical(scheme="S5", **kwargs)
    # The colour-conditioned drive changes the active occupancy relative to the
    # symmetric neighbour-difference scheme for this asymmetric environment.
    assert p6 != pytest.approx(p5)


def test_s6_drive_decreases_with_likewise_neighbours():
    # The defining property of S6: a site's chemical drive must decrease
    # monotonically as it gains neighbours of its OWN colour. Vary the likewise
    # count at zero unlike neighbours and check both colours.
    dmu0 = 1.5
    red_envs = [(n, 0) for n in range(MAX_NEIGHBOURS + 1)]
    blue_envs = [(0, n) for n in range(MAX_NEIGHBOURS + 1)]

    dmu_red = [d[0] for d in _drives("S6", dmu0, red_envs)]
    dmu_blue = [d[1] for d in _drives("S6", dmu0, blue_envs)]

    assert np.all(np.diff(dmu_red) < 0), dmu_red
    assert np.all(np.diff(dmu_blue) < 0), dmu_blue
    # Unperturbed with no likewise neighbours, and strongly damped with four.
    assert dmu_red[0] == pytest.approx(dmu0)
    assert dmu_red[-1] == pytest.approx(dmu0 * np.exp(-MAX_NEIGHBOURS))
    # Both colours are damped identically by their own likewise count.
    assert dmu_red == pytest.approx(dmu_blue)


def test_s6_drive_magnitude_decreases_for_a_negative_drive():
    # With dmu0 < 0 the drive increases towards zero, so the statement is about
    # magnitude -- state it that way so the test is sign-convention independent.
    dmu0 = -1.5
    envs = [(n, 0) for n in range(MAX_NEIGHBOURS + 1)]
    magnitudes = [abs(d[0]) for d in _drives("S6", dmu0, envs)]
    assert np.all(np.diff(magnitudes) < 0), magnitudes


def test_s6_drive_is_conditioned_on_likewise_not_unlike_neighbours():
    # Regression test for the swapped colour conditioning: a red site's drive
    # must depend only on n_red, and adding blue neighbours must leave it alone.
    dmu0 = 1.5
    (dmu_red_alone, _), (dmu_red_with_blues, _) = _drives(
        "S6", dmu0, [(1, 0), (1, 3)]
    )
    assert dmu_red_alone == pytest.approx(dmu_red_with_blues)

    # And a red site with red neighbours must be damped, not left unperturbed
    # (which is what conditioning on the unlike count produced at (2, 0)).
    (dmu_red, dmu_blue), = _drives("S6", dmu0, [(2, 0)])
    assert dmu_red == pytest.approx(dmu0 * np.exp(-2.0))
    assert dmu_blue == pytest.approx(dmu0)  # no blue neighbours -> undamped


def test_dmu_family_drives_decrease_in_their_own_neighbour_count():
    # S4 falls off with the total neighbour count and S5 with the neighbour
    # difference; neither is colour-conditioned, so both drives move together.
    dmu0 = 1.5
    s4 = _drives("S4", dmu0, [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)])
    assert np.all(np.diff([d[0] for d in s4]) < 0)
    assert all(red == pytest.approx(blue) for red, blue in s4)

    s5 = _drives("S5", dmu0, [(2, 2), (2, 1), (2, 0), (3, 0), (4, 0)])
    assert np.all(np.diff([d[0] for d in s5]) < 0)
    assert all(red == pytest.approx(blue) for red, blue in s5)


def test_k_family_rates_decrease_and_leave_the_drive_alone():
    # S2/S3 perturb the base rate k, not the drive.
    M = np.exp(1.5)
    for scheme, envs in [
        ("S2", [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]),   # total count
        ("S3", [(2, 2), (2, 1), (2, 0), (3, 0), (4, 0)]),   # difference
    ]:
        rates, drives = [], []
        for env in envs:
            M_red, M_blue, k = scheme_rescaled_drive_and_rate(
                scheme, M=M, k=1.0, environment=env
            )
            rates.append(k)
            drives.append((M_red, M_blue))
        assert np.all(np.diff(rates) < 0), (scheme, rates)
        assert all(r == pytest.approx(M) and b == pytest.approx(M)
                   for r, b in drives), scheme


def test_homogeneous_schemes_leave_the_drive_unperturbed():
    M = np.exp(1.5)
    for scheme in ("S0", "S1"):
        for env in [(0, 0), (2, 2), (4, 0)]:
            M_red, M_blue, k = scheme_rescaled_drive_and_rate(
                scheme, M=M, k=7.0, environment=env
            )
            assert (M_red, M_blue) == (M, M)
            assert k == 1.0   # S0/S1 use a unit base rate


def test_scheme_from_hrc_legacy_mapping():
    # Legacy (nesspy < 1.9.0) hrc_method catalogue.
    assert scheme_from_hrc(False, 91.0, legacy=True) == "S1"  # hrc off -> homogeneous
    assert scheme_from_hrc(False, float("nan"), legacy=True) == "S1"
    assert scheme_from_hrc(True, 91.0, legacy=True) == "S2"
    assert scheme_from_hrc(True, 93.0, legacy=True) == "S3"
    assert scheme_from_hrc(True, 3.0, legacy=True) == "S4"
    assert scheme_from_hrc(True, 6.0, legacy=True) == "S5"
    assert scheme_from_hrc(True, 7.0, legacy=True) == "S6"


def test_scheme_from_hrc_unknown_method_raises():
    with pytest.raises(NotImplementedError):
        scheme_from_hrc(True, 42.0, legacy=True)


def test_scheme_labels():
    # The short labels follow the S-numbering from the scheme note, and the
    # pre-rename spellings still resolve to them.
    assert scheme_short_label("S1") == "S1"
    assert scheme_short_label("HOMO") == "S1"
    assert scheme_short_label("SCHEME7") == "S6"
    assert scheme_math_label("HOMO") == r"$\mathcal{S}1$"


def test_thermos_normalises_legacy_scheme_names():
    # Legacy spellings are accepted but read back canonically.
    assert Thermos(method="HOMO").method == "S1"
    assert Thermos(method="SCHEME_91").method == "S2"
    assert Thermos(method="scheme7").method == "S6"
    with pytest.raises(ValueError):
        Thermos(method="NOPE")
