"""Resolve a driving scheme from the raw header fields of an ``out.csv``.

Usage::

    python resolve_scheme.py <hrc> <hrc_method> [nesspy_version]

and it prints the canonical scheme name (``S0``-``S6``) on stdout, or an error
message on stderr with exit code 1.

Why this exists: ``hrc_method`` numbers are **version-dependent** (nesspy 1.9.0
renamed the schemes, so legacy ``6.0`` is S5 while modern ``6.0`` is S6). The
mapping must therefore never be re-implemented in shell — ``catalog.sh`` greps
the three raw values out of the header and hands them to this script, which
resolves them through the single source of truth in ``schemes.py``.

Only ``nesspy_analysis.schemes`` is imported (it has no dependencies of its own,
not even pandas), so this stays fast enough to call once per run directory.
"""

import sys

from nesspy_analysis.schemes import is_legacy_scheme_numbering, scheme_from_hrc


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__, file=sys.stderr)
        return 1

    # `# hrc: False` in the header -> the run is undriven-per-scheme; anything
    # else is a truthy driving flag. Parsed leniently because the header spells
    # it as a Python bool.
    hrc = argv[0].strip().lower() in ("true", "1", "yes")

    try:
        hrc_method = float(argv[1])
    except ValueError:
        print(f"hrc_method '{argv[1]}' is not a number", file=sys.stderr)
        return 1

    # No version banner (very old output) -> is_legacy_scheme_numbering(None)
    # returns True, i.e. we assume the pre-1.9.0 catalogue.
    version = argv[2].strip() if len(argv) == 3 and argv[2].strip() else None
    legacy = is_legacy_scheme_numbering(version)

    try:
        print(scheme_from_hrc(hrc, hrc_method, legacy=legacy))
    except NotImplementedError as e:
        print(f"unknown hrc_method: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
