"""Run directories containing a mu whose simulations wrote no measurement rows.

A ``nesspy`` run that hits ``max_time`` before its interface finishes leaves an
``out.csv`` holding only the ``#`` header block and the column-name line -- no
measurement rows at all. This happens routinely at the deepest chemical
potentials of a *driven* sweep, where growth is slowest (it is exactly what
``RETHINKING_SUPERSAT/X_320_Y_80_3.0_D0.5_JHOM_-3.50_F0.0_K1.0`` shows at
mu = -6.90 and -6.85).

``get_data()`` has always skipped such a mu and carried on. These tests pin that
``get_thermos_from_file()`` skips it the same way, so one unfinished mu cannot
make an otherwise good run directory unanalyzable, and that a directory in which
*every* file is header-only fails with a message that says so.
"""
import pytest

from nesspy_analysis import DynamicalOrderDisorder


# One out.csv in the shape nesspy 1.9.1 writes it. `rows=False` produces the
# header-only file an unfinished mu leaves behind: identical header and column
# line, but no data.
def _out_csv(mu: str, dmu: str = "0.5", rows: bool = True) -> str:
    header = f"""\
#
# nesspy Version 1.9.1, Release Date: 2026/08/04
#
# jhom: -3.5
# jhet: -2.0
# fres: 0.0
# drive: {dmu}
# rate: 1.0
# xsize: 320.0
# ysize: 80.0
# hrc: True
# hrc_method: 3.0
# rswidth: 50
"""
    columns = (
        "mu,t,iter,exitcode,m,msquared,mu_cycles,root_seed,unique_seed,"
        "instance,gspeed,fres,dmu,k,hrc,hrc_method,rs,rs_width,version\n"
    )
    if not rows:
        return header + columns
    return header + columns + (
        f"{mu},1400000.0,103000000,0,0.18,0.03,21000000,322448,1,0,760000.0,"
        f"0.0,{dmu},1.0,True,3.0,True,50,1.9.1\n"
        f"{mu},1410000.0,103500000,0,0.24,0.06,21100000,322448,2,1,770000.0,"
        f"0.0,{dmu},1.0,True,3.0,True,50,1.9.1\n"
    )


def _make_run(tmp_path, mus_with_rows, mus_without_rows=()):
    """Build a run directory of mu-named subfolders, each holding one out.csv."""
    for mu in mus_with_rows:
        d = tmp_path / mu
        d.mkdir()
        (d / "out.csv").write_text(_out_csv(mu, rows=True))
    for mu in mus_without_rows:
        d = tmp_path / mu
        d.mkdir()
        (d / "out.csv").write_text(_out_csv(mu, rows=False))
    return DynamicalOrderDisorder(tmp_path.name, tmp_path)


def test_thermos_skips_header_only_files(tmp_path):
    # Two good mu plus two that produced nothing: the parameters still resolve,
    # and they resolve to the same values as if the empty files were absent.
    run = _make_run(tmp_path, ["-6.5", "-6.45"], ["-6.9", "-6.85"])
    thermos = run.get_thermos_from_file()

    assert thermos.dmu == pytest.approx(0.5)
    assert thermos.fres == pytest.approx(0.0)
    assert thermos.k == pytest.approx(1.0)
    assert thermos.jhom == pytest.approx(-3.5)
    assert thermos.jhet == pytest.approx(-2.0)
    assert thermos.method == "S3"  # modern numbering: hrc_method 3.0 -> S3


def test_thermos_matches_run_without_the_empty_files(tmp_path):
    # The skipped files must not perturb the detected parameters at all: the same
    # two good mu with and without two header-only neighbours give the same answer.
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    with_empty = _make_run(tmp_path / "a", ["-6.5", "-6.45"], ["-6.9", "-6.85"])
    without_empty = _make_run(tmp_path / "b", ["-6.5", "-6.45"])

    a = with_empty.get_thermos_from_file()
    b = without_empty.get_thermos_from_file()

    # Compared field by field: Thermos carries an epsilon_matrix ndarray, so the
    # dataclass __eq__ would raise on the ambiguous array truth value.
    for field in ("jhom", "jhet", "beta", "fres", "k", "dmu", "method",
                  "drive_reverse", "drive_scheme_reverse"):
        assert getattr(a, field) == getattr(b, field), field


def test_get_data_and_thermos_agree_on_which_mu_survive(tmp_path):
    # get_data() and get_thermos_from_file() must skip the *same* files, which is
    # the invariant the bug broke: get_data() coped, parameter detection did not.
    run = _make_run(tmp_path, ["-6.5", "-6.45"], ["-6.9", "-6.85"])

    data = run.get_data()
    assert len(data) == 2
    assert sorted(round(mu, 2) for mu in data["mu"]) == [-6.5, -6.45]

    run.get_thermos_from_file()  # must not raise


def test_all_files_header_only_raises_clear_error(tmp_path):
    # Nothing to detect parameters from: the error should say that, rather than
    # reporting an empty parameter set from the consistency checks.
    run = _make_run(tmp_path, [], ["-6.9", "-6.85"])

    with pytest.raises(ValueError, match="contain measurement rows"):
        run.get_thermos_from_file()
