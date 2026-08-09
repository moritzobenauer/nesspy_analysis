"""Canonical driving-scheme naming (S0-S6) and legacy ``out.csv`` compatibility.

A "driving scheme" fixes how the non-equilibrium drive is applied as a function
of the local environment: depending on the scheme either the base rate ``k`` or
the chemical drive ``dmu`` is rescaled by the neighbour counts. See
``dealing_with_different_schemes.md`` for the physics of each one.

Canonical names
---------------
Throughout this package a scheme is identified by its **manuscript name**
``"S0"`` ... ``"S6"``:

===== ==========================================================
S0    undriven / equilibrium reference (analysis-only, no drive)
S1    homogeneous driving (no spatial perturbation)
S2    k    rescaled by exp(-(n_red + n_blue))
S3    k    rescaled by exp(-|n_red - n_blue|)
S4    dmu  rescaled by exp(-(n_red + n_blue))
S5    dmu  rescaled by exp(-|n_red - n_blue|)
S6    dmu  rescaled by the likewise-neighbour count n' (colour-conditioned)
===== ==========================================================

The older internal spellings (``"NODRIVE"``, ``"HOMO"``, ``"SCHEME91"``,
``"SCHEME_3"``, ...) are still accepted everywhere and are normalised by
:func:`canonical_scheme`, so existing scripts and notebooks keep working.

Reading the scheme back out of an ``out.csv``
--------------------------------------------
In the raw data a scheme is encoded by the pair ``(hrc, hrc_method)``. The
meaning of the ``hrc_method`` *number* changed with **nesspy 1.9.0 (released
2026-08-03)**, which renamed the schemes to the manuscript convention:

========== ===================== =====================
hrc_method modern (>= 1.9.0)     legacy (< 1.9.0)
========== ===================== =====================
1.0        S1                    allosteric (no S-equivalent)
2.0        S2                    -
3.0        S3                    S4
4.0        S4                    -
5.0        S5                    -
6.0        S6                    S5
7.0        -                     S6
91.0       -                     S2
93.0       -                     S3
========== ===================== =====================

Note that ``3.0`` and ``6.0`` mean *different* schemes in the two conventions,
so the file's nesspy version has to be consulted before the number can be
interpreted; that is what the ``legacy`` flag of :func:`scheme_from_hrc` is for.
``nesspy_analysis.read_csv.is_legacy_output()`` determines it from the
``# nesspy Version ...`` header line of the file itself.

The inverse (backward) drive
----------------------------
nesspy 1.10.0 gave the backward reaction (inactive -> active) its own drive, and
1.10.1 started recording it in ``out.csv`` as the ``inverse_drive`` /
``inverse_scheme`` columns. It has its own scheme, resolved by
:func:`inverse_scheme_from_hrc` -- Δμ-family only, always in the manuscript
numbering. Output without those columns states no inverse drive, i.e.
:data:`NO_INVERSE_DRIVE` (``0.0``) with :data:`NO_INVERSE_DRIVE_SCHEME`
(``"S0"``).
"""

from __future__ import annotations

import re
from datetime import date

# Explicit, so that `from .schemes import *` in __init__.py does not also
# re-export the `re`/`date` imports as package attributes.
__all__ = [
    "NESSPY_SCHEME_RENAME_VERSION",
    "NESSPY_SCHEME_RENAME_DATE",
    "NESSPY_INVERSE_DRIVE_VERSION",
    "SCHEMES",
    "SCHEME_LABELS",
    "SCHEME_ALIASES",
    "MODERN_HRC_METHOD_TO_SCHEME",
    "LEGACY_HRC_METHOD_TO_SCHEME",
    "FROZEN_HRC_METHOD_TO_SCHEME",
    "DMU_FAMILY_SCHEMES",
    "K_FAMILY_SCHEMES",
    "NO_INVERSE_DRIVE",
    "NO_INVERSE_DRIVE_SCHEME",
    "canonical_scheme",
    "scheme_from_hrc",
    "inverse_scheme_from_hrc",
    "legacy_scheme_name",
    "scheme_short_label",
    "scheme_math_label",
    "scheme_description",
    "version_tuple",
    "parse_version_header",
    "is_legacy_scheme_numbering",
]

# ---------------------------------------------------------------------------
# The nesspy release that renamed the schemes to the manuscript convention.
# Output written *before* this release numbers its schemes with the old
# catalogue (see LEGACY_HRC_METHOD_TO_SCHEME below).
#
# The version is the primary discriminator and the release date is only the
# fallback: nesspy 1.8.0 was released on the same day (2026-08-03) as 1.9.0 but
# still used the old numbering, so a pure date comparison would misclassify it.
# ---------------------------------------------------------------------------
NESSPY_SCHEME_RENAME_VERSION: tuple[int, ...] = (1, 9, 0)
NESSPY_SCHEME_RENAME_DATE: date = date(2026, 8, 3)

# The nesspy release that started recording the inverse (backward) drive in
# out.csv: 1.10.1 (2026-08-04) added the `inverse_drive` / `inverse_scheme`
# columns after `k`. Output older than this states no inverse drive at all, and
# is read with the NO_INVERSE_DRIVE defaults below. Note that this release is
# *newer* than the scheme renaming, so an `inverse_scheme` number is always in
# the manuscript numbering -- there is no legacy catalogue for it.
NESSPY_INVERSE_DRIVE_VERSION: tuple[int, ...] = (1, 10, 1)


# canonical name -> (short label, LaTeX label for plots, human description).
SCHEME_LABELS: dict[str, tuple[str, str, str]] = {
    "S0": ("S0", r"$\mathcal{S}0$", "undriven / equilibrium reference"),
    "S1": ("S1", r"$\mathcal{S}1$", "homogeneous driving (no spatial perturbation)"),
    "S2": ("S2", r"$\mathcal{S}2$", "rate k rescaled by exp(-(n_red + n_blue))"),
    "S3": ("S3", r"$\mathcal{S}3$", "rate k rescaled by exp(-|n_red - n_blue|)"),
    "S4": ("S4", r"$\mathcal{S}4$", "drive dmu rescaled by exp(-(n_red + n_blue))"),
    "S5": ("S5", r"$\mathcal{S}5$", "drive dmu rescaled by exp(-|n_red - n_blue|)"),
    "S6": ("S6", r"$\mathcal{S}6$", "colour-conditioned drive dmu (likewise neighbours)"),
}

# Every canonical scheme name, in order.
SCHEMES: tuple[str, ...] = tuple(SCHEME_LABELS)

# Pre-rename internal spellings -> canonical name. Both the underscored and the
# bare form of every SCHEME* name occur in older scripts, so accept both.
SCHEME_ALIASES: dict[str, str] = {
    "NODRIVE": "S0",
    "NO_DRIVE": "S0",
    "HOMO": "S1",
    "HOMOGENEOUS": "S1",
    "SCHEME91": "S2",
    "SCHEME_91": "S2",
    "SCHEME93": "S3",
    "SCHEME_93": "S3",
    "SCHEME3": "S4",
    "SCHEME_3": "S4",
    "SCHEME6": "S5",
    "SCHEME_6": "S5",
    "SCHEME7": "S6",
    "SCHEME_7": "S6",
}

# hrc_method -> canonical name, for output written by nesspy >= 1.9.0, where the
# hrc_method number *is* the manuscript scheme number.
MODERN_HRC_METHOD_TO_SCHEME: dict[float, str] = {
    1.0: "S1",
    2.0: "S2",
    3.0: "S3",
    4.0: "S4",
    5.0: "S5",
    6.0: "S6",
}

# hrc_method -> canonical name, for output written by nesspy < 1.9.0. The
# remaining pre-rename methods (allosteric 1.0, red-only 2.0, the _EXP variants,
# ...) have no counterpart in this analysis package and raise below.
LEGACY_HRC_METHOD_TO_SCHEME: dict[float, str] = {
    91.0: "S2",  # LD on k
    93.0: "S3",  # LHOM on k
    3.0: "S4",   # LD on dmu
    6.0: "S5",   # LHOM on dmu
    7.0: "S6",   # LNN on dmu
}

# nesspy >= 1.9.0 also kept every pre-rename scheme alive behind a "99" prefix
# (old 3.0 -> 993.0, old 93.0 -> 9993.0, ...). Those that coincide with one of
# the manuscript schemes are mapped here; the rest have no S-equivalent.
FROZEN_HRC_METHOD_TO_SCHEME: dict[float, str] = {
    990.0: "S1",   # null dmu perturbation == no perturbation
    993.0: "S4",   # old 3.0
    996.0: "S5",   # old 6.0
    997.0: "S6",   # old 7.0 -- the *linear* pre-2026-08-04 S6, see note below
    9990.0: "S1",  # null k perturbation == no perturbation
    9991.0: "S2",  # old 91.0
    9993.0: "S3",  # old 93.0
}

# Which quantity a scheme's local perturbation acts on. S1 counts as dmu-family
# because it *is* the identity perturbation of dmu (nesspy's `spatial_dmu`
# returns its input unchanged at hrc_method 1.0), which is why it is a valid
# inverse-drive scheme; S0 is the analysis-only undriven reference and belongs to
# neither family.
DMU_FAMILY_SCHEMES: frozenset[str] = frozenset({"S1", "S4", "S5", "S6"})
K_FAMILY_SCHEMES: frozenset[str] = frozenset({"S2", "S3"})

# What an out.csv without the inverse-drive columns means: no drive on the
# backward (inactive -> active) reaction at all. exp(0.0) == 1.0 leaves every
# backward rate untouched, so S0 -- the undriven reference -- is the scheme of
# that channel, and every analysis of pre-1.10.1 data is unaffected.
NO_INVERSE_DRIVE: float = 0.0
NO_INVERSE_DRIVE_SCHEME: str = "S0"

# NOTE on S6: nesspy changed S6 from the linear form dmu_0 * (1 - n'/4) to the
# exponential dmu_0 * exp(-n') on 2026-08-04 (nesspy 1.9.1). Legacy hrc_method
# 7.0 and frozen 997.0 therefore refer to the linear form while modern
# hrc_method 6.0 refers to the exponential one. Both map to "S6" here because
# they are the same scheme in the manuscript; the functional form used by this
# package's own S6 implementations is documented at those call sites.


def canonical_scheme(method: str) -> str:
    """Normalise any accepted scheme spelling onto its canonical ``S*`` name.

    Accepts the canonical names (``"S3"``, case-insensitive) as well as every
    pre-rename spelling in :data:`SCHEME_ALIASES` (``"HOMO"``, ``"SCHEME_91"``,
    ...). Raises ``ValueError`` for anything else, so a typo cannot silently
    fall through to the wrong physics.

    Bare numbers are deliberately *not* accepted: ``3`` is ambiguous between the
    scheme name S3 and the ``hrc_method`` value 3.0 (which is S3 in modern but
    S4 in legacy output). Use :func:`scheme_from_hrc` for ``hrc_method`` values.
    """
    if method is None:
        raise ValueError("Driving scheme is None; expected one of " f"{list(SCHEMES)}")

    key = str(method).strip().upper().replace(" ", "")
    if key in SCHEME_LABELS:
        return key
    if key in SCHEME_ALIASES:
        return SCHEME_ALIASES[key]
    raise ValueError(
        f"Unknown driving scheme: {method!r}. Expected one of {list(SCHEMES)} "
        f"or a legacy alias {sorted(SCHEME_ALIASES)}."
    )


def scheme_from_hrc(hrc: bool, hrc_method: float, legacy: bool = False) -> str:
    """Map an ``out.csv`` ``(hrc, hrc_method)`` pair onto a canonical scheme.

    ``hrc`` inactive -> ``"S1"`` (homogeneous driving) regardless of
    ``hrc_method``, which is a free float in that case. When ``hrc`` is active
    the ``hrc_method`` number selects the scheme, interpreted with the *legacy*
    catalogue when ``legacy`` is true and with the manuscript catalogue
    otherwise -- see the module docstring for why that distinction matters.

    An ``hrc_method`` with no counterpart in this package raises
    ``NotImplementedError`` so a new scheme has to be registered deliberately.
    """
    if not hrc:
        return "S1"

    key = round(float(hrc_method), 1)
    if legacy:
        if key in LEGACY_HRC_METHOD_TO_SCHEME:
            return LEGACY_HRC_METHOD_TO_SCHEME[key]
        raise NotImplementedError(
            f"Active hrc with legacy hrc_method={hrc_method}; no driving-scheme "
            f"mapping exists. Known legacy methods: "
            f"{sorted(LEGACY_HRC_METHOD_TO_SCHEME)}."
        )

    if key in MODERN_HRC_METHOD_TO_SCHEME:
        return MODERN_HRC_METHOD_TO_SCHEME[key]
    if key in FROZEN_HRC_METHOD_TO_SCHEME:
        return FROZEN_HRC_METHOD_TO_SCHEME[key]
    raise NotImplementedError(
        f"Active hrc with hrc_method={hrc_method}; no driving-scheme mapping "
        f"exists. Known methods: {sorted(MODERN_HRC_METHOD_TO_SCHEME)} "
        f"(plus the frozen legacy band {sorted(FROZEN_HRC_METHOD_TO_SCHEME)}). "
        f"If this file predates nesspy 1.9.0, pass legacy=True."
    )


def inverse_scheme_from_hrc(
    hrc: bool, inverse_scheme: float, inverse_drive: float | None = None
) -> str:
    """Map an ``out.csv`` inverse-drive record onto a canonical scheme.

    The inverse (backward) drive of nesspy >= 1.10.0 carries its own scheme
    number, recorded as the ``inverse_scheme`` column / ``# inverse_drive_scheme``
    header entry. It is resolved like the forward one, with two differences:

    * **No legacy catalogue.** The inverse drive is newer than the scheme
      renaming (:data:`NESSPY_INVERSE_DRIVE_VERSION` > 1.9.0), so its number is
      always the manuscript numbering.
    * **Δμ-family only.** nesspy evaluates it through ``hrc.spatial_dmu``, so a
      k-family number (S2/S3) is invalid and raises ``ValueError`` there; it
      raises here too rather than being silently reinterpreted.

    ``hrc`` inactive → ``"S1"``: nesspy only perturbs the inverse drive inside its
    ``if hrc:`` branch (``nesspy/src/kmc.py``), so with hrc off the backward drive
    is homogeneous whatever ``inverse_scheme`` says.

    Passing ``inverse_drive`` reports a *zero* inverse drive as
    :data:`NO_INVERSE_DRIVE_SCHEME` (``"S0"``, the undriven reference): with
    ``exp(0.0) == 1.0`` the backward rates are untouched no matter which scheme
    the file names, so this is the same answer legacy output gets and keeps the
    two consistent. Omit it to resolve the recorded number unconditionally.
    """
    if inverse_drive is not None and float(inverse_drive) == 0.0:
        return NO_INVERSE_DRIVE_SCHEME

    scheme = scheme_from_hrc(hrc, inverse_scheme, legacy=False)
    if scheme in K_FAMILY_SCHEMES:
        raise ValueError(
            f"inverse_scheme={inverse_scheme} resolves to {scheme}, which "
            f"rescales the base rate k. The inverse drive is a Delta-mu drive, "
            f"so only {sorted(DMU_FAMILY_SCHEMES)} are valid (nesspy raises the "
            f"same way in hrc.spatial_dmu)."
        )
    return scheme


def legacy_scheme_name(scheme: str) -> str:
    """The pre-rename internal spelling of a canonical scheme (for messages)."""
    scheme = canonical_scheme(scheme)
    for old, new in SCHEME_ALIASES.items():
        # Return the bare (non-underscored) spelling, which is what the old
        # registry used, e.g. "S5" -> "SCHEME6".
        if new == scheme and "_" not in old:
            return old
    return scheme


def scheme_short_label(method: str) -> str:
    """Short scheme label (e.g. ``'S1'``) for summaries / filenames.

    Unknown spellings are passed through unchanged rather than raising, so that
    labelling a figure can never break an otherwise-finished analysis.
    """
    try:
        return SCHEME_LABELS[canonical_scheme(method)][0]
    except ValueError:
        return str(method)


def scheme_math_label(method: str) -> str:
    r"""LaTeX scheme label (e.g. ``'$\mathcal{S}1$'``) for plot legends/titles."""
    try:
        return SCHEME_LABELS[canonical_scheme(method)][1]
    except ValueError:
        return str(method)


def scheme_description(method: str) -> str:
    """One-line human-readable description of a driving scheme."""
    try:
        return SCHEME_LABELS[canonical_scheme(method)][2]
    except ValueError:
        return str(method)


# ---------------------------------------------------------------------------
# nesspy version header parsing.
#
# Every out.csv carries a banner line of the form
#     # nesspy Version 1.4.1, Release Date: 2025/11/02
# which is what tells us whether the hrc_method numbers in the file follow the
# legacy or the manuscript catalogue.
# ---------------------------------------------------------------------------

_VERSION_HEADER_RE = re.compile(
    r"nesspy\s+Version\s+(?P<version>[0-9][^\s,]*)"
    r"(?:\s*,\s*Release\s+Date:\s*(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2}))?",
    re.IGNORECASE,
)


def version_tuple(version: str) -> tuple[int, ...]:
    """Numeric prefix of a version string as a tuple, e.g. ``'1.9.0'`` -> ``(1, 9, 0)``.

    Trailing non-numeric components (``'1.9.0rc1'``) are dropped, which is
    enough to compare against the rename release.
    """
    parts: list[int] = []
    for chunk in str(version).strip().split("."):
        match = re.match(r"(\d+)", chunk)
        if match is None:
            break
        parts.append(int(match.group(1)))
    return tuple(parts)


def parse_version_header(line: str) -> tuple[str, date | None] | None:
    """Parse one ``# nesspy Version ...`` banner line.

    Returns ``(version_string, release_date_or_None)``, or ``None`` if the line
    is not a nesspy version banner.
    """
    match = _VERSION_HEADER_RE.search(line)
    if match is None:
        return None
    release_date = None
    if match.group("y"):
        release_date = date(
            int(match.group("y")), int(match.group("m")), int(match.group("d"))
        )
    return (match.group("version"), release_date)


def is_legacy_scheme_numbering(
    version: str | None = None, release_date: date | None = None
) -> bool:
    """Whether ``hrc_method`` numbers follow the legacy (pre-1.9.0) catalogue.

    The version wins when it is parseable; the release date is only consulted
    as a fallback (nesspy 1.8.0 shares the 2026-08-03 release date with the
    renaming 1.9.0 but still used the old numbering). Output with neither piece
    of information is assumed legacy -- the version banner has been written for
    far longer than the manuscript numbering has existed.
    """
    if version is not None:
        parsed = version_tuple(version)
        if parsed:
            return parsed < NESSPY_SCHEME_RENAME_VERSION
    if release_date is not None:
        return release_date < NESSPY_SCHEME_RENAME_DATE
    return True
