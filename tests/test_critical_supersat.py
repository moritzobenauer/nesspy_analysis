"""Errors on the critical supersaturation (DynamicalOrderDisorder.get_critical_supersat).

Two independent error estimates are checked against synthetic sigmoid data:

* the **resolution** error (returned value) -- the mean dphi spacing bracketing
  the inflection point; it depends only on the grid, so denser sampling halves
  it and noise leaves it unchanged; and
* the **covariance** error (``self.critical_supersat_cov_err``) -- the standard
  error on x0 from the fit; it is ~0 for clean data and grows with noise.

These exercise get_critical_supersat directly (no simulation volumes) by
injecting a pre-built ``self.data`` frame, so the object is constructed with
``__new__`` to skip the filesystem-scanning ``__init__``.
"""
import numpy as np
import pandas as pd
import pytest

from nesspy_analysis import sigmoid, fit_sigmoid
from nesspy_analysis.classes import DynamicalOrderDisorder

# Known ground-truth logistic. x0_true=0.5 is deliberately chosen NOT to land on
# any grid point of the linspaces below, so the inflection point always falls
# strictly between two samples and the resolution error is exactly half the
# local spacing.
L_TRUE, X0_TRUE, K_TRUE, B_TRUE = 1.0, 0.5, -3.0, 0.0


def _make_data(n, noise=0.0, seed=0):
    """A DataFrame of (dphi, m) sampling the ground-truth sigmoid on n points."""
    dphi = np.linspace(-4.0, 4.0, n)
    m = sigmoid(dphi, L_TRUE, X0_TRUE, K_TRUE, B_TRUE)
    if noise:
        m = m + np.random.default_rng(seed).normal(0.0, noise, size=m.shape)
    return pd.DataFrame({"dphi": dphi, "m": m})


def _run(df):
    """Run get_critical_supersat on an injected data frame, bypassing __init__."""
    obj = DynamicalOrderDisorder.__new__(DynamicalOrderDisorder)
    obj.data = df
    value, res_err = obj.get_critical_supersat()
    return obj, value, res_err


# --------------------------------------------------------------------------- #
# Resolution error (the returned value): grid-only, so it is exactly half the
# bracketing-interval width and independent of measurement noise.
# --------------------------------------------------------------------------- #

def test_resolution_error_is_half_the_local_spacing():
    # 21 points over [-4, 4] -> spacing 0.4; x0~0.5 sits between 0.4 and 0.8, so
    # the resolution error is exactly half the interval = 0.2.
    _, value, res_err = _run(_make_data(n=21))
    assert value == pytest.approx(X0_TRUE, abs=1e-3)
    assert res_err == pytest.approx(0.2, abs=1e-9)


def test_resolution_error_halves_when_sampling_doubles():
    # Doubling the sample density (spacing 0.4 -> 0.2) halves the resolution
    # error (0.2 -> 0.1): the whole point of the estimate.
    _, _, coarse = _run(_make_data(n=21))   # spacing 0.4
    _, _, fine = _run(_make_data(n=41))     # spacing 0.2
    assert coarse == pytest.approx(0.2, abs=1e-9)
    assert fine == pytest.approx(0.1, abs=1e-9)
    assert fine == pytest.approx(coarse / 2, rel=1e-6)


def test_resolution_error_is_insensitive_to_noise():
    # Same grid, added scatter: the inflection point stays in the same bracket,
    # so the grid-only resolution error is unchanged.
    _, _, clean = _run(_make_data(n=41))
    _, _, noisy = _run(_make_data(n=41, noise=0.03, seed=1))
    assert noisy == pytest.approx(clean, abs=1e-9)


def test_resolution_error_one_sided_when_extrapolated():
    # A monotone-but-unsaturated branch pushes the fitted inflection point below
    # the sampled range; only an upper neighbour exists, so the error is the
    # one-sided distance to the smallest sampled dphi.
    dphi = np.linspace(0.0, 4.0, 15)          # all samples >= 0
    m = sigmoid(dphi, L=1.0, x0=-3.0, k=-3.0, b=0.0)  # inflection at -3, off-grid
    _, value, res_err = _run(pd.DataFrame({"dphi": dphi, "m": m}))
    assert value < dphi.min()
    assert res_err == pytest.approx(dphi.min() - value, abs=1e-9)


# --------------------------------------------------------------------------- #
# Covariance error (self.critical_supersat_cov_err): statistical, so ~0 for
# clean data and monotone-increasing in the measurement noise.
# --------------------------------------------------------------------------- #

def test_covariance_error_is_tiny_for_clean_data():
    obj, _, _ = _run(_make_data(n=41))
    assert np.isfinite(obj.critical_supersat_cov_err)
    assert obj.critical_supersat_cov_err < 1e-3


def test_covariance_error_grows_with_noise():
    # More measurement scatter -> a less well-constrained inflection point ->
    # a larger covariance standard error. Clean < low-noise < high-noise.
    clean, _, _ = _run(_make_data(n=61))
    low, _, _ = _run(_make_data(n=61, noise=0.05, seed=2))
    high, _, _ = _run(_make_data(n=61, noise=0.15, seed=2))
    e_clean = clean.critical_supersat_cov_err
    e_low = low.critical_supersat_cov_err
    e_high = high.critical_supersat_cov_err
    assert 0.0 <= e_clean < e_low < e_high
    assert np.isfinite(e_high)


# --------------------------------------------------------------------------- #
# fit_sigmoid's return_cov plumbing that get_critical_supersat relies on.
# --------------------------------------------------------------------------- #

def test_fit_sigmoid_return_cov_shape_and_default():
    x = np.linspace(-4, 4, 60)
    y = sigmoid(x, L_TRUE, X0_TRUE, K_TRUE, B_TRUE)
    # Default: popt only (backward compatible).
    popt = fit_sigmoid(x, y)
    assert np.asarray(popt).shape == (4,)
    # return_cov=True: (popt, pcov) with a 4x4 covariance matrix.
    popt2, pcov = fit_sigmoid(x, y, return_cov=True)
    assert np.asarray(pcov).shape == (4, 4)
    assert np.sqrt(pcov[1, 1]) >= 0.0
