"""An in-memory stand-in for the SMB backend."""

import io
from typing import IO, Any


class FakeBackend:
    """Holds files in a dict, keyed by their full SMB path."""

    def __init__(self, files: dict[str, bytes] | None = None) -> None:
        self.files: dict[str, bytes] = dict(files or {})
        self.sessions: list[str] = []
        self.resets = 0
        self.fail_with: Exception | None = None

    def register_session(self, host: str, **kwargs: Any) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.sessions.append(host)

    def reset_connection_cache(self) -> None:
        self.resets += 1

    def listdir(self, path: str) -> list[str]:
        if self.fail_with is not None:
            raise self.fail_with
        prefix = path.rstrip("\\") + "\\"
        return [
            name[len(prefix) :]
            for name in self.files
            if name.startswith(prefix) and "\\" not in name[len(prefix) :]
        ]

    def open_file(self, path: str, mode: str) -> IO[Any]:
        if self.fail_with is not None:
            raise self.fail_with
        if "w" in mode:
            return _Writer(self, path)
        if path not in self.files:
            raise FileNotFoundError(path)
        return io.BytesIO(self.files[path])

    def rename(self, src: str, dst: str) -> None:
        self.files[dst] = self.files.pop(src)

    def remove(self, path: str) -> None:
        self.files.pop(path, None)

    def exists(self, path: str) -> bool:
        return path in self.files


class _Writer(io.BytesIO):
    def __init__(self, backend: FakeBackend, path: str) -> None:
        super().__init__()
        self._backend = backend
        self._path = path

    def close(self) -> None:
        self._backend.files[self._path] = self.getvalue()
        super().close()
