"""The errors a caller has to handle, and the translation into them.

There are four, and they are deliberately few. A caller reaching a file share
wants to distinguish "I was not configured", "I asked for something I am not
allowed to have", "the share did not answer" and "something is already there
and it is not mine" — and nothing finer. Everything the underlying library
raises is translated into one of these, so no caller has to import
`smbprotocol`'s exception tree to write a correct `except` clause.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from smbprotocol.exceptions import SMBException


class ShareError(Exception):
    """Base for everything this library raises."""


class ShareConfigError(ShareError):
    """Raised when the share is not configured.

    Distinct from unreachable: nothing was attempted, so nothing can be retried
    until a human supplies credentials.
    """


class PathNotAllowedError(ShareError):
    """Raised when a path falls outside every configured root."""


class ShareUnreachableError(ShareError):
    """Raised when the credentials are there and the share still did not answer.

    A share that will not answer is a fault, not an empty folder. Downstream the
    two are indistinguishable — both end with nothing new — so the failure is
    raised as itself rather than returned as an empty list.
    """


class ConflictingContentError(ShareError):
    """Raised when a file is already in place with different bytes.

    A retry of a completed write is success. A file under the same name holding
    *different* bytes is somebody else's, and overwriting it is the one
    unrecoverable thing this library could do.
    """


@contextmanager
def translated(what: str) -> Iterator[None]:
    """Turn whatever the SMB layer raises into `ShareUnreachableError`.

    Three exception types reach this point and the third is not obvious.
    `smbprotocol` catches the socket error during transport connection and
    re-raises it as a plain `ValueError` naming the server, so a host that does
    not resolve arrives as neither an `OSError` nor an `SMBException`. Without
    this, an unreachable host raises straight past a caller's `except` clause —
    and the caller records nothing, reports nothing, and leaves whatever it
    feeds looking as though the share had simply been empty.

    `ValueError` is broad, so keep the guarded block narrow: build paths
    outside it and put only the calls into the SMB layer inside.
    """
    try:
        yield
    except (OSError, SMBException, ValueError) as exc:
        raise ShareUnreachableError(f"{what}: {exc}") from exc
