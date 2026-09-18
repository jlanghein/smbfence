"""Share paths, as pure functions.

A share path arrives spelled whichever way its caller happens to hold it: with
backslashes from a Windows tool, with forward slashes from a config file, with
or without a leading separator. Comparing two of those spellings directly is
the bug this module exists to prevent, because the comparison that matters is
whether a path is inside an allowed root, and `"clients/acme"` must match
`"\\clients\\acme\\"` for that check to mean anything.

Nothing here touches a share, so all of it is tested without one.
"""

from collections.abc import Sequence
from typing import Final

from smbfence.errors import PathNotAllowedError

WINDOWS_SEPARATOR: Final[str] = "\\"
POSIX_SEPARATOR: Final[str] = "/"


def normalise(path: str) -> str:
    """One spelling for a share path, whichever separator the caller used."""
    return path.replace(WINDOWS_SEPARATOR, POSIX_SEPARATOR).strip(POSIX_SEPARATOR)


def to_windows(path: str) -> str:
    """The normalised path spelled the way SMB expects it."""
    return normalise(path).replace(POSIX_SEPARATOR, WINDOWS_SEPARATOR)


def unc(host: str, share: str) -> str:
    """The UNC prefix every resolved path is built on."""
    return f"{WINDOWS_SEPARATOR * 2}{host}{WINDOWS_SEPARATOR}{share}"


def is_within(path: str, allowed: Sequence[str]) -> bool:
    """Whether a path sits inside one of the allowed roots.

    A root matches itself and anything beneath it. The separator in the prefix
    test is what stops `clients/acme-holdings` from matching the root
    `clients/acme` — without it, any root would also admit every sibling whose
    name it happens to prefix.
    """
    candidate = normalise(path)
    return any(
        candidate == normalise(root) or candidate.startswith(normalise(root) + POSIX_SEPARATOR)
        for root in allowed
    )


PATH_NOT_ALLOWED: Final[str] = (
    "{path!r} is outside every configured root. A share holds more than one "
    "system's files, so this one reads only what it was told to."
)


def guard(path: str, allowed: Sequence[str]) -> str:
    """The normalised path, or `PathNotAllowedError` if it is out of bounds.

    Every path reaching the share passes through here. Returning the normalised
    form rather than `None` is what makes that enforceable: a caller cannot use
    a path it did not get back from this function.
    """
    if not is_within(path, allowed):
        raise PathNotAllowedError(PATH_NOT_ALLOWED.format(path=path))
    return normalise(path)
