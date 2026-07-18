"""FLEX / mean-field supersaturation theory (flex.calculate_dphi)."""
import numpy as np
import pytest

from nesspy_analysis import calculate_dphi, Thermos


def test_calculate_dphi_nodrive_is_vectorised_and_finite():
    mu = np.linspace(-2.0, 2.0, 25)
    dphi = calculate_dphi(mu, Thermos(method="NODRIVE"))
    assert dphi.shape == mu.shape
    assert np.all(np.isfinite(dphi))
    # dphi is monotone increasing in mu for the exact undriven branch.
    assert np.all(np.diff(dphi) > 0)


def test_calculate_dphi_homo_branch_runs():
    dphi = calculate_dphi(np.array([0.0, 1.0]), Thermos(method="HOMO", dmu=0.5))
    assert dphi.shape == (2,)
    assert np.all(np.isfinite(dphi))


def test_calculate_dphi_scheme_aliases_agree():
    # The underscored and bare scheme spellings must resolve identically.
    mu = np.array([0.5, 1.5])
    a = calculate_dphi(mu, Thermos(method="SCHEME_3", dmu=1.0))
    b = calculate_dphi(mu, Thermos(method="SCHEME3", dmu=1.0))
    assert np.allclose(a, b)


def test_calculate_dphi_unknown_scheme_raises():
    with pytest.raises(ValueError):
        calculate_dphi(np.array([0.0]), Thermos(method="NOPE"))
