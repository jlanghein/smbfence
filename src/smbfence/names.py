"""Choosing entries out of a directory listing, as pure functions.

A share filed by hand from both Windows and macOS accumulates metadata files
next to the real ones: `.DS_Store` and `._`-prefixed resource forks from macOS,
`Thumbs.db` and `desktop.ini` from Windows. They appear in every folder and
they are never what a caller asked for.

The second rule here is less obvious. Selecting by suffix and *excluding* by
prefix are different questions, and folding them into one test lets an excluded
file through the moment a caller asks by suffix alone. Where a share holds two
kinds of file under one extension — a booked export and a provisional one, say —
that mistake imports data that was never meant to be read as final.

Nothing here touches a share, so all of it is tested without one.
"""

from collections.abc import Iterable, Sequence
from typing import Final

APPLE_DOUBLE_PREFIX: Final[str] = "._"
NOISE_NAMES: Final[frozenset[str]] = frozenset(
    {".ds_store", "thumbs.db", "desktop.ini", ".spotlight-v100", ".trashes"}
)


def is_noise(name: str) -> bool:
    """Whether an entry is filesystem metadata rather than a file anyone filed."""
    lowered = name.lower()
    return lowered in NOISE_NAMES or lowered.startswith(APPLE_DOUBLE_PREFIX)


def matches(
    name: str,
    *,
    suffix: str | None = None,
    prefix: str | None = None,
    excluded_prefixes: Sequence[str] = (),
) -> bool:
    """Whether an entry is one a caller asked for.

    Exclusions are applied before the suffix test, never merged with it, so a
    caller asking only by suffix still does not receive an excluded file.
    """
    if is_noise(name):
        return False

    lowered = name.lower()
    if any(lowered.startswith(excluded.lower()) for excluded in excluded_prefixes):
        return False
    if prefix is not None and not lowered.startswith(prefix.lower()):
        return False
    return not (suffix is not None and not lowered.endswith(suffix.lower()))


def select(
    names: Iterable[str],
    *,
    suffix: str | None = None,
    prefix: str | None = None,
    excluded_prefixes: Sequence[str] = (),
) -> list[str]:
    """The matching entries, sorted.

    Sorted because a directory listing arrives in whatever order the server
    chose, and a caller that processes files in listing order would otherwise
    behave differently against two servers holding identical files.
    """
    return sorted(
        name
        for name in names
        if matches(name, suffix=suffix, prefix=prefix, excluded_prefixes=excluded_prefixes)
    )
