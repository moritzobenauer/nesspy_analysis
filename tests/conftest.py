"""Shared fixtures for the nesspy_analysis test suite.

The package is exercised through its installed form (``import nesspy_analysis``),
so these tests require ``uv sync`` to have installed the editable package. They
avoid the external simulation volumes entirely by synthesising the small lattices
and out.csv files each test needs.
"""
import numpy as np
import pytest

# A minimal, self-consistent out.csv: the data-row fres/k/dmu columns match the
# header's `# fres`/`# rate`/`# drive`, which read_csv() cross-checks.
OUT_CSV = """\
# jhom : -3.5
# jhet : -2.0
# fres : -20.0
# drive : 0.0
# rate : 1.0
# xsize : 100
# ysize : 80
m,msquared,mu,gspeed,fres,k,dmu,rs_width
0.5,0.30,1.0,2.0,-20.0,1.0,0.0,0
0.4,0.25,1.0,2.5,-20.0,1.0,0.0,0
"""


@pytest.fixture
def out_csv(tmp_path):
    """Write OUT_CSV to a temp file and return its Path."""
    f = tmp_path / "out.csv"
    f.write_text(OUT_CSV)
    return f


@pytest.fixture
def blue_block_lattice():
    """10x10 lattice that is empty except for one 3x3 blue (value 2) block."""
    lat = np.zeros((10, 10), dtype=int)
    lat[2:5, 2:5] = 2  # a single 4-connected cluster of size 9
    return lat


@pytest.fixture
def checkerboard():
    """10x10 red/blue checkerboard: every nearest-neighbour bond is a 1-2 bond."""
    lat = np.indices((10, 10)).sum(axis=0) % 2  # 0/1 parity
    return np.where(lat == 0, 1, 2)
