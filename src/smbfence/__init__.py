"""A guarded SMB share client."""

from smbfence.backend import SmbClientBackend
from smbfence.client import ShareClient, SmbBackend, share_connection
from smbfence.config import ShareConfig
from smbfence.errors import (
    ConflictingContentError,
    PathNotAllowedError,
    ShareConfigError,
    ShareError,
    ShareUnreachableError,
)

__all__ = [
    "ConflictingContentError",
    "PathNotAllowedError",
    "ShareClient",
    "ShareConfig",
    "ShareConfigError",
    "ShareError",
    "ShareUnreachableError",
    "SmbBackend",
    "SmbClientBackend",
    "share_connection",
]
