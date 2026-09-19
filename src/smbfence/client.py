"""Reaching the share, guarded.

Every path passes through `paths.guard` before it reaches the SMB layer, and
every call into that layer is wrapped so its three failure modes arrive as one.

The backend is a Protocol rather than a direct `smbclient` import, so the whole
client is testable without a server. That is not only convenient: code that can
only be exercised against a real share tends not to be exercised at all, and
this is code whose failure modes matter.
"""

import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import IO, Any, Final, Protocol

from smbfence import names, paths
from smbfence.config import ShareConfig
from smbfence.errors import ConflictingContentError, translated

logger: Final[logging.Logger] = logging.getLogger(__name__)

TEMP_SUFFIX: Final[str] = ".partial"


class SmbBackend(Protocol):
    """The part of `smbclient` this library uses."""

    def listdir(self, path: str) -> list[str]: ...
    def open_file(self, path: str, mode: str) -> IO[Any]: ...
    def rename(self, src: str, dst: str) -> None: ...
    def remove(self, path: str) -> None: ...
    def exists(self, path: str) -> bool: ...


class ShareClient:
    """Reads and writes within a fixed set of allowed roots."""

    def __init__(self, base: str, allowed: Sequence[str], backend: SmbBackend) -> None:
        self._base = base
        self._allowed = tuple(allowed)
        self._backend = backend

    def _resolve(self, path: str) -> str:
        """The full SMB path, or `PathNotAllowedError`."""
        safe = paths.to_windows(paths.guard(path, self._allowed))
        return f"{self._base}{paths.WINDOWS_SEPARATOR}{safe}"

    def list_files(
        self,
        directory: str,
        *,
        suffix: str | None = None,
        prefix: str | None = None,
        excluded_prefixes: Sequence[str] = (),
    ) -> list[str]:
        """The matching entries in an allowed directory, sorted."""
        full = self._resolve(directory)
        with translated(f"listing {directory}"):
            entries = self._backend.listdir(full)
        return names.select(
            entries, suffix=suffix, prefix=prefix, excluded_prefixes=excluded_prefixes
        )

    def read_file(self, path: str) -> bytes:
        """The bytes of one file in an allowed directory."""
        full = self._resolve(path)
        with translated(f"reading {path}"), self._backend.open_file(full, mode="rb") as handle:
            return handle.read()

    def write_file(self, path: str, content: bytes) -> None:
        """Publish `content` at `path`, atomically, never overwriting.

        Written beside itself and renamed into place, so a transfer that stops
        half way leaves nothing under the final name. Without that, a link
        dropping mid-write leaves a truncated file where a whole one is
        expected, and every retry afterwards reads it back, finds bytes that
        differ, and refuses for good.

        A file already in place with the same bytes is success: a retry of a
        completed write is not an error. One holding *different* bytes belongs
        to somebody else, and is left exactly where it is.
        """
        full = self._resolve(path)
        temp = full + TEMP_SUFFIX

        with translated(f"writing {path}"):
            if self._backend.exists(full):
                with self._backend.open_file(full, mode="rb") as handle:
                    existing = handle.read()
                if existing == content:
                    logger.debug("%s already in place with identical bytes", path)
                    return
                raise ConflictingContentError(
                    f"{path!r} is already in place with different bytes and was not overwritten"
                )

            with self._backend.open_file(temp, mode="wb") as handle:
                handle.write(content)
            self._backend.rename(temp, full)


@contextmanager
def share_connection(
    config: ShareConfig, backend: SmbBackend, *, allowed: Sequence[str] | None = None
) -> Iterator[ShareClient]:
    """A client for the configured share, with the session dropped afterwards.

    The connection is dropped after every use. A hand-run script exits and takes
    its sockets with it; a long-lived process does not, and `smbclient` caches
    connections per host. A session that died quietly between two runs would be
    handed back to the next one, turning a recoverable blip into a fault that
    persists until somebody restarts the process.
    """
    config.require()
    roots = tuple(allowed if allowed is not None else config.allowed_paths)

    register = getattr(backend, "register_session", None)
    reset = getattr(backend, "reset_connection_cache", None)

    with translated(f"connecting to {config.host}"):
        if register is not None:
            register(
                config.host,
                username=config.user,
                password=config.password.get_secret_value(),
                port=config.port,
            )
    try:
        yield ShareClient(base=paths.unc(config.host, config.share), allowed=roots, backend=backend)
    finally:
        if reset is not None:
            reset()
