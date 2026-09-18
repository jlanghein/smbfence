"""The errors a caller has to handle.

There are four, and they are deliberately few. A caller reaching a file share
wants to distinguish "I was not configured", "I asked for something I am not
allowed to have", "the share did not answer" and "something is already there
and it is not mine" — and nothing finer. Everything the underlying library
raises is translated into one of these, so no caller has to import
`smbprotocol`'s exception tree to write a correct `except` clause.
"""


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
