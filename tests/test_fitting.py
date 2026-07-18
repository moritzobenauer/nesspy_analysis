"""Fitting primitives: closed-form values and synthetic round-trip recovery."""
import numpy as np
import pytest

from nesspy_analysis import (
    lorentzian, fit_lorentzian, sigmoid, fit_sigmoid, polynomial,
)


def test_lorentzian_peaks_at_x0():
    # At x = x0 the Lorentzian equals its amplitude A; it is symmetric about x0.
    assert lorentzian(2.0, x0=2.0, gamma=0.5, A=3.0) == pytest.approx(3.0)
    assert lorentzian(2.3, 2.0, 0.5, 3.0) == pytest.approx(lorentzian(1.7, 2.0, 0.5, 3.0))


def test_sigmoid_inflection_and_saturation():
    # Logistic value at the inflection point is b + L/2; tails saturate to b and b+L.
    assert sigmoid(1.0, L=4.0, x0=1.0, k=2.0, b=0.5) == pytest.approx(0.5 + 4.0 / 2)
    assert sigmoid(1e6, 4.0, 1.0, 2.0, 0.5) == pytest.approx(0.5)      # k>0 -> b
    assert sigmoid(-1e6, 4.0, 1.0, 2.0, 0.5) == pytest.approx(0.5 + 4.0)  # -> b+L


def test_polynomial_is_cubic_about_x0():
    # Only the offset (x - x0) enters; at x = x0 every term vanishes.
    assert polynomial(3.0, a=1.0, b=1.0, c=1.0, x0=3.0) == pytest.approx(0.0)
    assert polynomial(5.0, 2.0, 0.0, 0.0, 3.0) == pytest.approx(2.0 * (5.0 - 3.0))


def test_fit_lorentzian_recovers_peak_location():
    x = np.linspace(-5, 5, 200)
    y = lorentzian(x, x0=1.3, gamma=0.7, A=2.0)
    x0, gamma, A = fit_lorentzian(x, y)
    assert x0 == pytest.approx(1.3, abs=1e-3)
    assert abs(gamma) == pytest.approx(0.7, abs=1e-3)
    assert A == pytest.approx(2.0, abs=1e-3)


def test_fit_lorentzian_rejects_bad_input():
    with pytest.raises(ValueError):
        fit_lorentzian(np.array([]), np.array([]))
    with pytest.raises(ValueError):
        fit_lorentzian(np.array([1.0, 2.0]), np.array([1.0]))


@pytest.mark.parametrize("k_true", [3.0, -3.0])  # decreasing and increasing
def test_fit_sigmoid_recovers_inflection_both_directions(k_true):
    x = np.linspace(-4, 4, 120)
    y = sigmoid(x, L=1.0, x0=0.6, k=k_true, b=0.0)
    L, x0, k, b = fit_sigmoid(x, y)
    assert x0 == pytest.approx(0.6, abs=1e-3)
    assert np.sign(k) == np.sign(k_true)


def test_fit_sigmoid_rejects_bad_input():
    with pytest.raises(ValueError):
        fit_sigmoid([], [])
    with pytest.raises(ValueError):
        fit_sigmoid([1.0, 2.0, 3.0], [1.0, 2.0])
