"""The real SMB backend, wired to `smbclient`.

`smbclient` is not quite usable as a backend directly: `listdir`, `open_file`
and `rename` sit on the module, but `exists` lives on `smbclient.path`. Passing
the module straight in therefore satisfies the type checker's structural view
of it and fails at runtime on the first write.

This adapter is the one place that knows where each function actually lives.
"""

from typing import IO, Literal

import smbclient
import smbclient.path


class SmbClientBackend:
    """Delegates to `smbclient`, gathering its two namespaces into one."""

    def listdir(self, path: str) -> list[str]:
        return smbclient.listdir(path)

    def open_file(self, path: str, mode: Literal["rb", "wb"]) -> IO[bytes]:
        return smbclient.open_file(path, mode=mode)

    def rename(self, src: str, dst: str) -> None:
        smbclient.rename(src, dst)

    def exists(self, path: str) -> bool:
        return smbclient.path.exists(path)

    def register_session(self, host: str, username: str, password: str, port: int) -> None:
        smbclient.register_session(host, username=username, password=password, port=port)

    def reset_connection_cache(self) -> None:
        smbclient.reset_connection_cache()
