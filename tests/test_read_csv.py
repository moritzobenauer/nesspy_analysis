"""out.csv header parsing, aggregation, and derived growth speed."""
import numpy as np
import pytest

from nesspy_analysis import (
    read_csv, get_m_vals, get_epsilon, get_epsilon_het, get_df, get_dmu, get_k,
    get_lattice_dimensions,
)


def test_header_parsers(out_csv):
    assert get_epsilon(out_csv) == -3.5
    assert get_epsilon_het(out_csv) == -2.0
    assert get_df(out_csv) == -20.0        # `# fres`
    assert get_dmu(out_csv) == 0.0         # `# drive`
    assert get_k(out_csv) == 1.0           # `# rate`
    assert get_lattice_dimensions(out_csv) == [100, 80, 8000]


def test_get_m_vals_returns_mean_mu_and_raw_array(out_csv):
    mu, m_vals = get_m_vals(out_csv)
    assert mu == pytest.approx(1.0)
    assert np.allclose(np.sort(m_vals), [0.4, 0.5])


def test_read_csv_aggregates_and_derives_growth_speed(out_csv):
    # Deterministic path: no bootstrap, use the full frame.
    df, header = read_csv(out_csv, n_samples=1.0, bootstrap=False)

    assert df["m"].iloc[0] == pytest.approx(0.45)     # mean of 0.5, 0.4
    assert df["m2"].iloc[0] == pytest.approx(0.275)   # mean of 0.30, 0.25
    assert df["susc"].iloc[0] == pytest.approx(0.275 - 0.45**2)

    # growth_speed = L_y^2 * 2 / <t>, with L_y = ysize = 80 and <t> = 2.25.
    t_mean = (2.0 + 2.5) / 2
    assert df["growth_speed"].iloc[0] == pytest.approx(80**2 * 2 / t_mean)
    assert header["lattice_y"] == 80 and header["jhom"] == -3.5


def test_read_csv_missing_file_raises(tmp_path):
    with pytest.raises(ValueError):
        read_csv(tmp_path / "nope.csv")
