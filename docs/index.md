# smbfence

A guarded SMB share client for Python: **allowlisted paths, atomic writes, and one
failure mode instead of three.**

```python
from smbfence import ShareConfig, SmbClientBackend, share_connection

config = ShareConfig()  # SMB_HOST, SMB_SHARE, SMB_USER, SMB_PASSWORD

with share_connection(config, SmbClientBackend(), allowed=["clients/acme"]) as share:
    for name in share.list_files("clients/acme/bank", suffix=".sta", excluded_prefixes=["VMK_"]):
        data = share.read_file(f"clients/acme/bank/{name}")

    share.write_file("clients/acme/out/invoice.pdf", pdf_bytes)
```

## Why this exists

A Windows file share is a normal way to move documents between an accounting system and
the people who work in it. Reaching one from Python is easy. Reaching one *safely*
involves four problems that are not obvious until they have bitten you.

| Problem | What goes wrong | Page |
|---|---|---|
| A share holds more than one system's files | A wandering scan ingests somebody else's records into your books | [Allowlisting paths](guide/allowlisting.md) |
| The failure modes do not look like failures | An unreachable host raises a bare `ValueError` past your `except` clause | [Failure modes](guide/failures.md) |
| A hand-filed share is full of things nobody filed | `.DS_Store` and `._` forks arrive as if they were data | [Selecting entries](guide/selecting.md) |
| An interrupted write leaves something that looks finished | A truncated file under the final name, refused forever after | [Atomic writes](guide/writing.md) |

## Design

```
errors ──┬──► paths ──┐
         └──► names ──┴──► config ──► client
```

Dependencies flow one way. `paths` and `names` are pure functions, tested without a
share. The SMB backend is a `Protocol`, not a direct import, so the client is exercisable
in memory too — code that can only be tested against a real server tends not to be tested
at all, and this is code whose failure modes matter.

Three runtime dependencies: `smbprotocol`, `pydantic`, `pydantic-settings`. A library
that guards access to a file share should be cheap to audit.

## Errors

| Error | Meaning |
|---|---|
| `ShareConfigError` | Not configured. Nothing was attempted; nothing can be retried until a human acts |
| `PathNotAllowedError` | Outside every configured root |
| `ShareUnreachableError` | Configured, and the share did not answer |
| `ConflictingContentError` | Something is already there and it is not ours |

All inherit `ShareError`.

## Install

```bash
uv add smbfence
```

See [Getting Started](getting-started.md).
