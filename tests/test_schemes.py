"""Canonical S0-S6 scheme naming and legacy out.csv backward compatibility.

The nesspy 1.9.0 release (2026-08-03) renamed the driving schemes, which changed
the meaning of the ``hrc_method`` numbers written into every out.csv. These tests
pin both catalogues, the version gate that decides between them, and the
remapping notice printed for legacy folders.
"""
from datetime import date

import pytest

from nesspy_analysis.schemes import (
    canonical_scheme,
    is_legacy_scheme_numbering,
    legacy_scheme_name,
    parse_version_header,
    scheme_description,
    scheme_from_hrc,
    version_tuple,
)
from nesspy_analysis.read_csv import (
    get_hrc,
    get_nesspy_version,
    is_legacy_output,
    report_legacy_output,
    reset_legacy_notices,
)


# A header block in the shape nesspy writes it, parameterised by version banner
# and hrc entries so a test can synthesise legacy and modern output alike.
def _out_csv(version_line: str, hrc: str = "False", hrc_method: str = "1.0") -> str:
    return f"""\
#
# {version_line}
# MLO @ Princeton University, 2026
#
# jhom: -3.5
# jhet: -2.0
# fres: -20.0
# drive: 0.0
# rate: 1.0
# xsize: 320.0
# ysize: 80.0
# hrc: {hrc}
# hrc_method: {hrc_method}
# rswidth: 35
m,msquared,mu,gspeed,fres,k,dmu,rs_width
0.5,0.30,1.0,2.0,-20.0,1.0,0.0,35
0.4,0.25,1.0,2.5,-20.0,1.0,0.0,35
"""


@pytest.fixture(autouse=True)
def _clear_notices():
    # The legacy notice is printed once per directory for the lifetime of the
    # process, so reset the cache around every test.
    reset_legacy_notices()
    yield
    reset_legacy_notices()


# --- canonical naming ------------------------------------------------------


@pytest.mark.parametrize(
    "given, expected",
    [
        ("S0", "S0"), ("s3", "S3"), (" S6 ", "S6"),
        ("NODRIVE", "S0"),
        ("HOMO", "S1"),
        ("SCHEME91", "S2"), ("SCHEME_91", "S2"),
        ("SCHEME93", "S3"), ("SCHEME_93", "S3"),
        ("SCHEME3", "S4"), ("SCHEME_3", "S4"),
        ("SCHEME6", "S5"), ("SCHEME_6", "S5"),
        ("SCHEME7", "S6"), ("SCHEME_7", "S6"),
    ],
)
def test_canonical_scheme_accepts_legacy_spellings(given, expected):
    assert canonical_scheme(given) == expected


def test_canonical_scheme_rejects_unknown_and_bare_numbers():
    # Bare numbers are ambiguous between the S-name and the hrc_method value
    # (hrc_method 3.0 is S3 in modern but S4 in legacy output), so they raise.
    for bad in ["NOPE", "3", 3, None, ""]:
        with pytest.raises(ValueError):
            canonical_scheme(bad)


def test_legacy_scheme_name_round_trip():
    assert legacy_scheme_name("S1") == "HOMO"
    assert legacy_scheme_name("S4") == "SCHEME3"
    assert legacy_scheme_name("S6") == "SCHEME7"


def test_scheme_description_mentions_the_perturbed_quantity():
    assert "k" in scheme_description("S2")
    assert "dmu" in scheme_description("S4")


# --- the two hrc_method catalogues ----------------------------------------


@pytest.mark.parametrize(
    "hrc_method, expected", [(1.0, "S1"), (2.0, "S2"), (3.0, "S3"),
                             (4.0, "S4"), (5.0, "S5"), (6.0, "S6")]
)
def test_scheme_from_hrc_modern(hrc_method, expected):
    assert scheme_from_hrc(True, hrc_method, legacy=False) == expected


@pytest.mark.parametrize(
    "hrc_method, expected", [(91.0, "S2"), (93.0, "S3"), (3.0, "S4"),
                             (6.0, "S5"), (7.0, "S6")]
)
def test_scheme_from_hrc_legacy(hrc_method, expected):
    assert scheme_from_hrc(True, hrc_method, legacy=True) == expected


def test_the_same_number_means_different_schemes_in_each_catalogue():
    # This is the whole reason the version gate exists: hrc_method 3.0 was LD on
    # dmu (S4) before the renaming and is LHOM on k (S3) after it.
    assert scheme_from_hrc(True, 3.0, legacy=True) == "S4"
    assert scheme_from_hrc(True, 3.0, legacy=False) == "S3"
    assert scheme_from_hrc(True, 6.0, legacy=True) == "S5"
    assert scheme_from_hrc(True, 6.0, legacy=False) == "S6"


def test_inactive_hrc_is_always_homogeneous():
    for legacy in (True, False):
        assert scheme_from_hrc(False, 7.0, legacy=legacy) == "S1"
        assert scheme_from_hrc(False, float("nan"), legacy=legacy) == "S1"


@pytest.mark.parametrize(
    "hrc_method, expected", [(990.0, "S1"), (993.0, "S4"), (996.0, "S5"),
                             (997.0, "S6"), (9991.0, "S2"), (9993.0, "S3")]
)
def test_frozen_legacy_band_maps_to_its_scheme(hrc_method, expected):
    # nesspy >= 1.9.0 kept the pre-rename schemes behind a "99" prefix.
    assert scheme_from_hrc(True, hrc_method, legacy=False) == expected


def test_pre_rename_numbers_are_rejected_in_modern_output():
    # 91.0 was a real legacy method but is not a modern one; reading it as if it
    # were modern must fail loudly rather than pick the wrong scheme.
    with pytest.raises(NotImplementedError):
        scheme_from_hrc(True, 91.0, legacy=False)


# --- the version gate ------------------------------------------------------


def test_version_tuple_parses_numeric_prefix():
    assert version_tuple("1.9.0") == (1, 9, 0)
    assert version_tuple("1.10.1") == (1, 10, 1)
    assert version_tuple("1.9.0rc1") == (1, 9, 0)


def test_parse_version_header():
    assert parse_version_header("# nesspy Version 1.4.1, Release Date: 2025/11/02") == (
        "1.4.1", date(2025, 11, 2)
    )
    # The banner without a release date still yields the version.
    assert parse_version_header("# nesspy Version 1.9.0") == ("1.9.0", None)
    assert parse_version_header("# jhom: -3.5") is None


def test_is_legacy_scheme_numbering_uses_version_over_date():
    assert is_legacy_scheme_numbering("1.4.1", date(2025, 11, 2)) is True
    assert is_legacy_scheme_numbering("1.9.0", date(2026, 8, 3)) is False
    assert is_legacy_scheme_numbering("1.10.1", date(2026, 8, 4)) is False
    # nesspy 1.8.0 shares the 2026-08-03 release date with the renaming 1.9.0 but
    # still wrote the old numbering -- the version has to win here.
    assert is_legacy_scheme_numbering("1.8.0", date(2026, 8, 3)) is True
    # Date-only fallback, and the assume-legacy default.
    assert is_legacy_scheme_numbering(None, date(2026, 1, 16)) is True
    assert is_legacy_scheme_numbering(None, None) is True


# --- reading the version and hrc entries off a file ------------------------


def test_get_nesspy_version_from_legacy_file(tmp_path):
    f = tmp_path / "out.csv"
    f.write_text(_out_csv("nesspy Version 1.4.1, Release Date: 2025/11/02"))
    version = get_nesspy_version(f)
    assert version.version == "1.4.1"
    assert version.release_date == date(2025, 11, 2)
    assert version.legacy_schemes is True
    assert is_legacy_output(f) is True


def test_get_nesspy_version_from_modern_file(tmp_path):
    f = tmp_path / "out.csv"
    f.write_text(_out_csv("nesspy Version 1.10.1, Release Date: 2026/08/04"))
    assert get_nesspy_version(f).legacy_schemes is False
    assert is_legacy_output(f) is False


def test_file_without_banner_is_treated_as_legacy(tmp_path):
    f = tmp_path / "out.csv"
    f.write_text(_out_csv("MLO @ Princeton University"))
    version = get_nesspy_version(f)
    assert version.version is None and version.legacy_schemes is True


def test_get_hrc_reads_both_entries_exactly(tmp_path):
    # "# hrc_method" also starts with "# hrc", so the keys must not be confused.
    f = tmp_path / "out.csv"
    f.write_text(
        _out_csv("nesspy Version 1.4.1, Release Date: 2025/11/02",
                 hrc="True", hrc_method="6.0")
    )
    assert get_hrc(f) == (True, 6.0)


def test_get_hrc_returns_none_when_absent(tmp_path):
    f = tmp_path / "out.csv"
    f.write_text("# jhom: -3.5\nm,mu\n0.5,1.0\n")
    assert get_hrc(f) is None


# --- the remapping notice --------------------------------------------------


def test_report_legacy_output_remaps_and_prints_once(tmp_path, capsys):
    f = tmp_path / "out.csv"
    f.write_text(
        _out_csv("nesspy Version 1.4.1, Release Date: 2025/11/02",
                 hrc="True", hrc_method="6.0")
    )
    # Legacy hrc_method 6.0 is S5 (it would be S6 under the modern catalogue).
    assert report_legacy_output(f) == "S5"

    out = capsys.readouterr().out
    assert str(tmp_path) in out
    assert "1.4.1" in out and "hrc_method=6.0" in out and "S5" in out

    # A second read of the same folder stays quiet.
    assert report_legacy_output(f) == "S5"
    assert capsys.readouterr().out == ""


def test_report_legacy_output_is_silent_for_modern_files(tmp_path, capsys):
    f = tmp_path / "out.csv"
    f.write_text(
        _out_csv("nesspy Version 1.10.1, Release Date: 2026/08/04",
                 hrc="True", hrc_method="6.0")
    )
    assert report_legacy_output(f) is None
    assert capsys.readouterr().out == ""


def test_parent_notice_suppresses_child_notices(tmp_path, capsys):
    # A notice for the run directory must silence its per-mu subfolders.
    from nesspy_analysis.read_csv import notify_legacy_schemes

    child = tmp_path / "-6.75"
    child.mkdir()
    f = child / "out.csv"
    f.write_text(
        _out_csv("nesspy Version 1.4.1, Release Date: 2025/11/02",
                 hrc="True", hrc_method="7.0")
    )
    assert notify_legacy_schemes(tmp_path, "run directory notice") is True
    assert report_legacy_output(f) == "S6"
    assert "run directory notice" in capsys.readouterr().out


def test_report_legacy_run_prints_once_for_the_whole_run(tmp_path, capsys):
    from nesspy_analysis.read_csv import report_legacy_run

    files = []
    for mu in ("-6.5", "-6.4", "-6.3"):
        d = tmp_path / mu
        d.mkdir()
        f = d / "out.csv"
        f.write_text(
            _out_csv("nesspy Version 1.5.2, Release Date: 2025/11/14",
                     hrc="True", hrc_method="6.0")
        )
        files.append(f)

    assert report_legacy_run(tmp_path, files) is True
    out = capsys.readouterr().out
    assert out.count("[nesspy_analysis]") == 1
    assert "3/3 out.csv files" in out and "-> S5" in out

    # The run-level notice silences the per-file notices of every mu subfolder.
    for f in files:
        assert report_legacy_output(f) == "S5"
    assert capsys.readouterr().out == ""


def test_report_legacy_run_survives_unmappable_hrc_method(tmp_path, capsys):
    # A legacy hrc_method with no scheme in this package must still be reported
    # (get_thermos_from_file is where the NotImplementedError belongs).
    from nesspy_analysis.read_csv import report_legacy_run

    f = tmp_path / "out.csv"
    f.write_text(
        _out_csv("nesspy Version 1.5.2, Release Date: 2025/11/14",
                 hrc="True", hrc_method="94.0")
    )
    assert report_legacy_run(tmp_path, [f]) is True
    assert "legacy scheme catalogue" in capsys.readouterr().out


def test_dynamical_order_disorder_announces_legacy_run_at_init(tmp_path, capsys):
    from nesspy_analysis import DynamicalOrderDisorder

    d = tmp_path / "-6.5"
    d.mkdir()
    (d / "out.csv").write_text(
        _out_csv("nesspy Version 1.5.2, Release Date: 2025/11/14",
                 hrc="True", hrc_method="7.0")
    )
    DynamicalOrderDisorder("legacy_run", tmp_path)
    out = capsys.readouterr().out
    assert out.count("[nesspy_analysis]") == 1
    assert "-> S6" in out


def test_read_csv_reports_scheme_provenance_in_header(tmp_path):
    from nesspy_analysis import read_csv

    f = tmp_path / "out.csv"
    f.write_text(
        _out_csv("nesspy Version 1.4.1, Release Date: 2025/11/02",
                 hrc="True", hrc_method="91.0")
    )
    _, header = read_csv(f, n_samples=1.0, bootstrap=False)
    assert header["nesspy_version"] == "1.4.1"
    assert header["legacy_schemes"] is True
    assert header["scheme"] == "S2"
