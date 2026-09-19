# Failure modes

## Three exceptions, and the third is not obvious

`smbprotocol` raises `OSError` and `SMBException` where you would expect. It also catches
the socket error during transport connection and re-raises it as a plain **`ValueError`**
naming the server.

So a host that does not resolve arrives as **neither** of the two types you guarded
against.

```python
except (OSError, SMBException):   # looks complete. is not.
```

Left untranslated, an unreachable host raises straight past the caller's `except` clause.
Nothing is recorded, nothing is reported, and whatever the import feeds is left looking
as though the share had merely been empty.

## One error instead

```python
from smbfence.errors import translated, ShareUnreachableError

with translated("listing clients/acme"):
    entries = backend.listdir(full_path)
```

All three arrive as `ShareUnreachableError`, with the original preserved as `__cause__`
and the attempted operation named in the message.

!!! warning "Keep the guarded block narrow"
    `ValueError` is broad. Build paths *outside* the block and put only calls into the
    SMB layer inside it, or you will swallow programming errors along with connection
    failures.

## A share that will not answer is a fault, not an empty folder

Downstream the two are indistinguishable — both end with nothing new in the ledger. So
the failure is raised as itself rather than returned as an empty list.

This is the difference between an overview reporting *"no new statements today"* and
*"the share has not been readable since Tuesday"*. Only one of those gets fixed.

## Not configured is distinct from unreachable

```python
config.require()  # ShareConfigError if any credential is missing
```

Nothing was attempted, so nothing can be retried until a human supplies credentials. A
caller that retries an unconfigured share on a timer will retry forever.

## The connection is dropped after every use

```python
with share_connection(config, SmbClientBackend(), allowed=roots) as share:
    ...
# session reset here, always — including on exception
```

A hand-run script exits and takes its sockets with it. A long-lived process does not, and
`smbclient` caches connections per host.

A session that died quietly between two runs would be handed back to the next one,
turning a recoverable blip into a fault that persists **until somebody restarts the
process**. That is a bad failure: it looks like a broken share and it is a broken cache.
