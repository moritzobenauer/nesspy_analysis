"""FLEX / mean-field supersaturation theory (flex.calculate_dphi)."""
import numpy as np
import pytest

from nesspy_analysis import calculate_dphi, Thermos


def test_calculate_dphi_nodrive_is_vectorised_and_finite():
    mu = np.linspace(-2.0, 2.0, 25)
    dphi = calculate_dphi(mu, Thermos(method="S0"))
    assert dphi.shape == mu.shape
    assert np.all(np.isfinite(dphi))
    # dphi is monotone increasing in mu for the exact undriven branch.
    assert np.all(np.diff(dphi) > 0)


def test_calculate_dphi_homo_branch_runs():
    dphi = calculate_dphi(np.array([0.0, 1.0]), Thermos(method="S1", dmu=0.5))
    assert dphi.shape == (2,)
    assert np.all(np.isfinite(dphi))


@pytest.mark.parametrize("scheme", ["S0", "S1", "S2", "S3", "S4", "S5", "S6"])
def test_calculate_dphi_every_scheme_branch_runs(scheme):
    dphi = calculate_dphi(np.array([0.0, 1.0]), Thermos(method=scheme, dmu=1.0))
    assert dphi.shape == (2,)
    assert np.all(np.isfinite(dphi))


def test_calculate_dphi_scheme_aliases_agree():
    # The canonical name, the bare and the underscored pre-rename spellings must
    # all resolve to the same branch (legacy SCHEME3 == S4).
    mu = np.array([0.5, 1.5])
    a = calculate_dphi(mu, Thermos(method="SCHEME_3", dmu=1.0))
    b = calculate_dphi(mu, Thermos(method="SCHEME3", dmu=1.0))
    c = calculate_dphi(mu, Thermos(method="S4", dmu=1.0))
    assert np.allclose(a, b) and np.allclose(a, c)


def test_s6_uses_the_exponential_not_the_linear_form():
    # S6 is exponential in the likewise-neighbour count n' (nesspy hrc_method
    # 6.0), so at the mean-field n' = 2 it rescales dmu by exp(-2) -- the same
    # rescaling S4/S5 get. It must NOT use the old linear dmu_0 * (1 - n'/4),
    # which gave dmu/2 here.
    mu = np.array([0.5, 1.5])
    s6 = calculate_dphi(mu, Thermos(method="S6", dmu=1.0, k=1.0, fres=0.0))

    # S1 uses dmu as read, so it provides the reference value for each form.
    exponential = calculate_dphi(
        mu, Thermos(method="S1", dmu=np.exp(-2.0), k=1.0, fres=0.0)
    )
    linear = calculate_dphi(mu, Thermos(method="S1", dmu=0.5, k=1.0, fres=0.0))

    assert np.allclose(s6, exponential)
    assert not np.allclose(s6, linear)


def test_dmu_family_schemes_agree_at_mean_field():
    # S4, S5 and S6 are the same exponential suppression of dmu driven by three
    # different neighbour counts, which coincide at two neighbours.
    mu = np.array([0.5, 1.5])
    dphis = [
        calculate_dphi(mu, Thermos(method=s, dmu=1.0, k=1.0, fres=0.0))
        for s in ("S4", "S5", "S6")
    ]
    assert np.allclose(dphis[0], dphis[1]) and np.allclose(dphis[0], dphis[2])


def test_calculate_dphi_k_and_dmu_families_differ():
    # S2/S3 rescale k while S4/S5 rescale dmu, so with both k and dmu non-zero
    # the two families must not coincide. fres=0 (F=1) keeps the inert states
    # populated; at the default fres=-20 every F-weighted term is ~1e-9 and the
    # branches agree to within floating-point noise.
    mu = np.array([0.5, 1.5])
    k_family = calculate_dphi(mu, Thermos(method="S2", dmu=1.0, k=1.0, fres=0.0))
    dmu_family = calculate_dphi(mu, Thermos(method="S4", dmu=1.0, k=1.0, fres=0.0))
    assert not np.allclose(k_family, dmu_family)


def test_calculate_dphi_unknown_scheme_raises():
    with pytest.raises(ValueError):
        calculate_dphi(np.array([0.0]), Thermos(method="NOPE"))
