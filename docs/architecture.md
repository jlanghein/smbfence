# Architecture

## Layering

```
errors ──┬──► paths ──┐
         └──► names ──┴──► config ──► client
```

Dependencies flow one way. If A → B → C, then C may import B and A, but A may not import
C. That single rule eliminates circular imports without anyone having to think about
them.

| Module | Role | Touches the network |
|---|---|---|
| `errors` | The four exceptions, and translation into them | No |
| `paths` | Normalisation, allowlist check, UNC assembly | No |
| `names` | Entry selection out of a directory listing | No |
| `config` | Credentials, as a Pydantic model | No |
| `client` | The guarded read and write surface | Yes |

`errors` is the leaf — it imports nothing from the package. Everything else builds on it.

## The pure core

`paths` and `names` contain no I/O at all. That is not an aesthetic choice: the rules
they encode are precisely the ones that are hard to get right and expensive to get wrong,
and rules that can only be exercised against a live share do not get exercised.

Roughly two thirds of this library's logic is reachable without a network.

## The backend is a Protocol

```python
class SmbBackend(Protocol):
    def listdir(self, path: str) -> list[str]: ...
    def open_file(self, path: str, mode: str) -> IO[Any]: ...
    def rename(self, src: str, dst: str) -> None: ...
    def remove(self, path: str) -> None: ...
    def exists(self, path: str) -> bool: ...
```

The client never imports `smbclient`. It takes whatever satisfies that Protocol, which in
production is the `smbclient` module itself and in tests is a dictionary.

```python
from smbfence import ShareClient

client = ShareClient(base=r"\\server\share", allowed=["clients/acme"], backend=fake)
```

## Testing

64 tests, none of which need a server.

| Area | How |
|---|---|
| `paths`, `names` | Direct — pure functions |
| `config` | Direct — a Pydantic model |
| `client` reads and writes | In-memory backend holding files in a dict |
| Failure translation | Fake backend raising each of the three exception types |
| Connection lifecycle | Fake counting session registrations and resets |

The atomic-write behaviour is tested the way it actually fails: identical bytes already
present, conflicting bytes already present, and the absence of a `.partial` file once a
write completes.

## Naming

Layers are named by role, not by technology. `client.py`, not `smb.py`; `adapters`, not
`smbprotocol`. Roles are stable; technologies change.
