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
