# smbfence

A guarded SMB share client for Python: allowlisted paths, atomic writes, and one
failure mode instead of three.

```python
from smbfence import ShareConfig, SmbClientBackend, share_connection

config = ShareConfig()  # reads SMB_HOST, SMB_SHARE, SMB_USER, SMB_PASSWORD

with share_connection(config, SmbClientBackend(), allowed=["clients/acme"]) as share:
    for name in share.list_files("clients/acme/bank", suffix=".sta", excluded_prefixes=["VMK_"]):
        data = share.read_file(f"clients/acme/bank/{name}")

    share.write_file("clients/acme/out/invoice.pdf", pdf_bytes)
```

## Why this exists

A Windows file share is a normal way to move documents between an accounting
system and the people who work in it. Reaching one from Python is easy;
reaching one *safely* turns out to involve four problems that are not obvious
until they have bitten you.

### A share holds more than one system's files

The usual shape is one drive, many folders, several systems reading from it. A
recursive scan that wanders out of its own folder does not merely return too
much — it ingests somebody else's records into your books, and nothing
downstream can tell that happened.

Every path here passes through an allowlist first. `guard()` returns the
normalised path rather than a boolean, so the check cannot be skipped by
accident: a caller has no path to use except the one it got back.

### The failure modes do not look like failures

`smbprotocol` raises `OSError` and `SMBException` as you would expect. It also
catches the socket error during transport connection and re-raises it as a
plain **`ValueError`** naming the server — so a host that does not resolve
arrives as neither of the two you guarded against.

Left untranslated, that raises straight past your `except` clause: nothing is
recorded, nothing is reported, and whatever the import feeds is left looking as
though the share had merely been empty. A share that will not answer is a
fault, not an empty folder, and this library raises it as one.

### A hand-filed share is full of things nobody filed

Filed from both Windows and macOS, a share accumulates `.DS_Store`, `._`
resource forks, `Thumbs.db` and `desktop.ini` in every folder.

Selecting by suffix and *excluding* by prefix are also different questions, and
merging them lets an excluded file through the moment a caller asks by suffix
alone. Where a share holds a booked export and a provisional one under the same
extension, that mistake imports figures that were never final.

### An interrupted write leaves something that looks finished

Files are written beside themselves and renamed into place. Without that, a
link dropping mid-write leaves a truncated file under the final name, and every
retry afterwards reads it back, finds bytes that differ, and refuses for good.

A file already in place with identical bytes is success — a retry of a
completed write is not an error. One holding *different* bytes belongs to
somebody else and is left exactly where it is. Overwriting that is the one
unrecoverable thing this library could do, so it does not.

## Design

Dependencies flow one way: `errors` ← `paths` / `names` ← `config` ← `client`.

`paths` and `names` are pure functions, tested without a share. The SMB backend
is a `Protocol`, not a direct import, so the client is exercisable in memory
too — code that can only be tested against a real server tends not to be
tested at all, and this is code whose failure modes matter.

Three runtime dependencies: `smbprotocol`, `pydantic`, `pydantic-settings`. A
library that guards access to a file share should be cheap to audit.

## Install

```bash
uv add smbfence
```

## Configuration

Read from the environment or a `secrets.env` file, prefixed `SMB_`:

| Variable | Meaning |
|---|---|
| `SMB_HOST` | Server hostname |
| `SMB_SHARE` | Share name |
| `SMB_USER` | Username |
| `SMB_PASSWORD` | Password, held as a `SecretStr` |
| `SMB_PORT` | Defaults to 445 |
| `SMB_ALLOWED_PATHS` | Roots this process may read |

`config.is_configured` answers "should anything be attempted at all", which a
caller often needs before it has a connection to ask.

## Errors

| Error | Meaning |
|---|---|
| `ShareConfigError` | Not configured. Nothing was attempted; nothing can be retried until a human acts |
| `PathNotAllowedError` | Outside every configured root |
| `ShareUnreachableError` | Configured, and the share did not answer |
| `ConflictingContentError` | Something is already there and it is not ours |

All inherit `ShareError`.

## Development

```bash
uv sync --extra dev
uv run --extra dev ruff format .
uv run --extra dev ruff check --fix .
uv run --extra dev ty check src
uv run --extra dev pytest
```

Run the tools through `uv run`, not `uvx` — `uvx` pins nothing and resolves the
newest release on every invocation, so the checks can change behaviour with
nothing in the repository changing.

See [`AGENTS.md`](AGENTS.md) for the conventions CI enforces.

## Licence

MIT
