"""The inverse (backward) drive recorded by nesspy >= 1.10.1.

nesspy 1.10.0 gave the backward inactive -> active reaction its own chemical
drive, and 1.10.1 started writing it into ``out.csv`` as the ``inverse_drive`` /
``inverse_scheme`` columns (inserted after ``k``). These tests pin how the two are
read, how the scheme number is resolved, and -- most importantly -- that output
*without* those columns still reads as an undriven backward channel
``(0.0, "S0")``, so every data set analyzed before this existed is unaffected.
"""
import pytest

from nesspy_analysis import Thermos, DynamicalOrderDisorder, read_csv
from nesspy_analysis.read_csv import get_inverse_drive, get_inverse_drive_and_scheme
from nesspy_analysis.schemes import (
    NO_INVERSE_DRIVE,
    NO_INVERSE_DRIVE_SCHEME,
    inverse_scheme_from_hrc,
)


# An out.csv in the shape nesspy >= 1.10.1 writes it: the full modern column list
# (see nesspy/src/fileio.py:create_out_csv) plus the matching header block, which
# read_csv() cross-checks the fres/k/dmu columns against.
def _modern_out_csv(
    inverse_drive: str = "0.0",
    inverse_scheme: str = "1.0",
    hrc: str = "True",
    hrc_method: str = "6.0",
    dmu: str = "1.5",
    with_columns: bool = True,
) -> str:
    header = f"""\
#
# nesspy Version 1.10.1, Release Date: 2026/08/04
#
# jhom: -3.5
# jhet: -2.0
# fres: -20.0
# drive: {dmu}
# rate: 1.0
# xsize: 320.0
# ysize: 80.0
# hrc: {hrc}
# hrc_method: {hrc_method}
# inverse_drive: {inverse_drive}
# inverse_drive_scheme: {inverse_scheme}
# rswidth: 35
"""
    if with_columns:
        return header + (
            "mu,t,iter,exitcode,m,msquared,mu_cycles,root_seed,unique_seed,"
            "instance,gspeed,fres,dmu,k,inverse_drive,inverse_scheme,hrc,"
            "hrc_method,rs,rs_width,version\n"
            f"-6.5,10.0,100,0,0.50,0.30,1,1,1,0,2.0,-20.0,{dmu},1.0,"
            f"{inverse_drive},{inverse_scheme},{hrc},{hrc_method},True,35,1.10.1\n"
            f"-6.5,11.0,110,0,0.40,0.25,1,1,2,1,2.5,-20.0,{dmu},1.0,"
            f"{inverse_drive},{inverse_scheme},{hrc},{hrc_method},True,35,1.10.1\n"
        )
    # Same file without the two new columns (what a legacy writer produces).
    return header + (
        "mu,t,iter,exitcode,m,msquared,mu_cycles,root_seed,unique_seed,"
        "instance,gspeed,fres,dmu,k,hrc,hrc_method,rs,rs_width,version\n"
        f"-6.5,10.0,100,0,0.50,0.30,1,1,1,0,2.0,-20.0,{dmu},1.0,"
        f"{hrc},{hrc_method},True,35,1.10.1\n"
        f"-6.5,11.0,110,0,0.40,0.25,1,1,2,1,2.5,-20.0,{dmu},1.0,"
        f"{hrc},{hrc_method},True,35,1.10.1\n"
    )


def _write_run(tmp_path, text, mu="-6.5"):
    """Write one out.csv into a mu-named subfolder, as a real run is laid out."""
    d = tmp_path / mu
    d.mkdir()
    f = d / "out.csv"
    f.write_text(text)
    return f


# --- resolving the inverse-drive scheme number ------------------------------


@pytest.mark.parametrize(
    "inverse_scheme, expected",
    [(1.0, "S1"), (4.0, "S4"), (5.0, "S5"), (6.0, "S6"),
     (990.0, "S1"), (996.0, "S5")],   # incl. the frozen legacy band
)
def test_inverse_scheme_from_hrc_resolves_dmu_family(inverse_scheme, expected):
    # A nonzero inverse drive with hrc active: the number selects the scheme, in
    # the manuscript numbering (the inverse drive is newer than the renaming).
    assert inverse_scheme_from_hrc(True, inverse_scheme, 0.5) == expected


def test_inverse_scheme_without_hrc_is_homogeneous():
    # nesspy only perturbs the inverse drive inside its `if hrc:` branch, so with
    # hrc off the backward drive is homogeneous whatever the number says.
    assert inverse_scheme_from_hrc(False, 6.0, 0.5) == "S1"


def test_zero_inverse_drive_reads_as_undriven():
    # exp(0.0) == 1.0 leaves every backward rate untouched, so a zero inverse
    # drive is S0 regardless of the scheme the file names -- the same answer
    # output without the columns gets.
    assert inverse_scheme_from_hrc(True, 6.0, 0.0) == NO_INVERSE_DRIVE_SCHEME
    # Omitting the drive resolves the recorded number unconditionally.
    assert inverse_scheme_from_hrc(True, 6.0) == "S6"


@pytest.mark.parametrize("inverse_scheme", [2.0, 3.0])
def test_k_family_inverse_scheme_raises(inverse_scheme):
    # The inverse drive is a Delta-mu drive; nesspy's spatial_dmu rejects S2/S3
    # for it, and so do we rather than reinterpreting the number.
    with pytest.raises(ValueError):
        inverse_scheme_from_hrc(True, inverse_scheme, 0.5)


def test_unknown_inverse_scheme_raises():
    with pytest.raises(NotImplementedError):
        inverse_scheme_from_hrc(True, 42.0, 0.5)


# --- reading the pair out of a file ----------------------------------------


def test_get_inverse_drive_reads_the_columns(tmp_path):
    f = tmp_path / "out.csv"
    f.write_text(_modern_out_csv(inverse_drive="0.75", inverse_scheme="5.0"))
    assert get_inverse_drive(f) == (0.75, 5.0)
    assert get_inverse_drive_and_scheme(f) == (0.75, "S5")


def test_get_inverse_drive_falls_back_to_the_header(tmp_path):
    # nesspy >= 1.10.0 writes the header entries with the rest of the merged
    # simulation input, so a file can state them without having the columns.
    f = tmp_path / "out.csv"
    f.write_text(
        _modern_out_csv(inverse_drive="0.75", inverse_scheme="4.0",
                        with_columns=False)
    )
    assert get_inverse_drive(f) == (0.75, 4.0)
    assert get_inverse_drive_and_scheme(f) == (0.75, "S4")


def test_get_inverse_drive_is_none_for_legacy_output(out_csv):
    # The shared legacy fixture states neither the columns nor the header entries.
    assert get_inverse_drive(out_csv) is None
    assert get_inverse_drive_and_scheme(out_csv) == (
        NO_INVERSE_DRIVE, NO_INVERSE_DRIVE_SCHEME
    )


def test_inconsistent_inverse_drive_column_raises(tmp_path):
    # The inverse drive is a simulation input, written unchanged into every row,
    # so two different values in one out.csv mean the file cannot be trusted.
    f = tmp_path / "out.csv"
    f.write_text(
        "# inverse_drive: 0.5\n"
        "m,msquared,mu,gspeed,fres,k,dmu,inverse_drive,inverse_scheme,rs_width\n"
        "0.5,0.30,-6.5,2.0,-20.0,1.0,1.5,0.5,1.0,35\n"
        "0.4,0.25,-6.5,2.5,-20.0,1.0,1.5,0.9,1.0,35\n"
    )
    with pytest.raises(ValueError, match="inverse_drive"):
        get_inverse_drive(f)


# --- read_csv() and Thermos ------------------------------------------------


def test_read_csv_reports_the_inverse_drive(tmp_path):
    f = tmp_path / "out.csv"
    f.write_text(_modern_out_csv(inverse_drive="0.75", inverse_scheme="6.0"))
    _, header = read_csv(f, n_samples=1.0, bootstrap=False)
    assert header["drive_reverse"] == 0.75
    assert header["drive_scheme_reverse"] == "S6"
    assert header["scheme"] == "S6"          # the forward scheme is untouched


def test_read_csv_defaults_the_inverse_drive_for_legacy_output(out_csv):
    _, header = read_csv(out_csv, n_samples=1.0, bootstrap=False)
    assert header["drive_reverse"] == 0.0
    assert header["drive_scheme_reverse"] == "S0"


def test_thermos_inverse_drive_defaults_to_undriven():
    t = Thermos()
    assert (t.drive_reverse, t.drive_scheme_reverse) == (0.0, "S0")


def test_thermos_normalises_the_inverse_scheme_name():
    assert Thermos(drive_scheme_reverse="HOMO").drive_scheme_reverse == "S1"
    with pytest.raises(ValueError):
        Thermos(drive_scheme_reverse="NOPE")


# --- detection across a whole run directory --------------------------------


def test_get_thermos_from_file_detects_the_inverse_drive(tmp_path):
    for mu in ("-6.5", "-6.4"):
        _write_run(
            tmp_path,
            _modern_out_csv(inverse_drive="0.75", inverse_scheme="5.0",
                            hrc="True", hrc_method="5.0"),
            mu=mu,
        )
    thermos = DynamicalOrderDisorder("modern_run", tmp_path).get_thermos_from_file()
    assert thermos.method == "S5"
    assert thermos.drive_reverse == 0.75
    assert thermos.drive_scheme_reverse == "S5"


def test_get_thermos_from_file_defaults_for_output_without_the_columns(tmp_path):
    _write_run(tmp_path, _modern_out_csv(with_columns=False, hrc="False"))
    thermos = DynamicalOrderDisorder("no_inverse", tmp_path).get_thermos_from_file()
    assert thermos.drive_reverse == 0.0
    assert thermos.drive_scheme_reverse == "S0"


def test_get_thermos_from_file_rejects_a_mixed_inverse_drive(tmp_path):
    # Two mu folders driven differently in the backward channel are not one run.
    _write_run(tmp_path, _modern_out_csv(inverse_drive="0.75"), mu="-6.5")
    _write_run(tmp_path, _modern_out_csv(inverse_drive="0.25"), mu="-6.4")
    with pytest.raises(ValueError, match="drive_reverse"):
        DynamicalOrderDisorder("mixed_run", tmp_path).get_thermos_from_file()
