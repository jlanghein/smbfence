# Getting Started

## Install

```bash
uv add smbfence
```

Python 3.13 or later.

## Configure

Credentials are read from the environment, or from a `secrets.env` file, prefixed `SMB_`.

| Variable | Meaning | Default |
|---|---|---|
| `SMB_HOST` | Server hostname | — |
| `SMB_SHARE` | Share name | — |
| `SMB_USER` | Username | — |
| `SMB_PASSWORD` | Password, held as a `SecretStr` | — |
| `SMB_PORT` | Port | `445` |
| `SMB_ALLOWED_PATHS` | Roots this process may read | `()` |

```bash
# secrets.env — never commit this
SMB_HOST=fileserver.example.internal
SMB_SHARE=accounting
SMB_USER=svc-import
SMB_PASSWORD=...
```

!!! warning "The allowlist is not optional"
    A share with no configured roots can reach nothing. That is deliberate — see
    [Allowlisting paths](guide/allowlisting.md).

## Check before you connect

`is_configured` answers "should anything be attempted at all", which a caller often needs
before it has a connection to ask.

```python
from smbfence import ShareConfig

config = ShareConfig()
if not config.is_configured:
    ...  # nothing to retry until a human supplies credentials
```

## Read

```python
from smbfence import SmbClientBackend, share_connection

with share_connection(config, SmbClientBackend(), allowed=["clients/acme"]) as share:
    names = share.list_files("clients/acme/bank", suffix=".sta")
    for name in names:
        data = share.read_file(f"clients/acme/bank/{name}")
```

The session is registered on entry and dropped on exit — see
[Failure modes](guide/failures.md#the-connection-is-dropped-after-every-use).

## Write

```python
with share_connection(config, SmbClientBackend(), allowed=["clients/acme"]) as share:
    share.write_file("clients/acme/out/invoice-2026-001.pdf", pdf_bytes)
```

Written beside itself and renamed into place. A file already there with identical bytes
is success; one with different bytes is left alone. See [Atomic writes](guide/writing.md).

## Handle the four errors

```python
from smbfence import (
    ConflictingContentError,
    PathNotAllowedError,
    ShareConfigError,
    ShareUnreachableError,
)

try:
    with share_connection(config, SmbClientBackend(), allowed=roots) as share:
        share.write_file(path, content)
except ShareConfigError:
    ...  # nothing was attempted
except PathNotAllowedError:
    ...  # a bug in the caller, not a transient fault
except ShareUnreachableError:
    ...  # retry later; this is a fault, not an empty folder
except ConflictingContentError:
    ...  # somebody else's file is under that name
```

## Test without a share

`paths` and `names` are pure. The client takes its SMB backend as a `Protocol`, so an
in-memory fake is enough for the rest — see [Architecture](architecture.md#testing).
