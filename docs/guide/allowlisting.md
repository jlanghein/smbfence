# Allowlisting paths

## The problem

The usual shape of a business file share is one drive, many folders, several systems
reading from it. A tax advisor's working drive holds one client's bank statements beside
another's; a property manager's drive holds accounting exports beside scanned leases.

A recursive scan that wanders out of its own folder does not merely return too much. It
**ingests somebody else's records into your books**, and nothing downstream can tell that
happened. The import succeeds. The numbers are wrong. Nobody finds out for a quarter.

## The guard

Every path reaching the SMB layer passes through `guard()` first.

```python
from smbfence.paths import guard

guard("clients/acme/bank", ["clients/acme"])  # "clients/acme/bank"
guard("clients/other", ["clients/acme"])  # PathNotAllowedError
```

`guard` returns the **normalised path** rather than a boolean. That is what makes the
check enforceable rather than advisory: a caller has no path to use except the one it got
back, so the check cannot be skipped by forgetting to call it.

## Spelling

A share path arrives spelled whichever way its caller happens to hold it — backslashes
from a Windows tool, forward slashes from a config file, with or without a leading
separator. Comparing two spellings directly is the bug this prevents.

```python
from smbfence.paths import normalise

normalise(r"\clients\acme\\")  # "clients/acme"
normalise("/clients/acme/")  # "clients/acme"
```

## The separator in the prefix test

A root matches itself and anything beneath it:

```python
is_within("clients/acme", ["clients/acme"])  # True
is_within("clients/acme/bank/2026", ["clients/acme"])  # True
```

But not a sibling whose name it merely prefixes:

```python
is_within("clients/acme-holdings", ["clients/acme"])  # False
```

!!! note "Why that case matters"
    Without the separator in the prefix test, the root `clients/acme` would also admit
    `clients/acme-holdings`, `clients/acme-old`, and every other folder starting with
    those characters. On a share organised by client name, that is not a hypothetical.

## An empty allowlist reaches nothing

```python
is_within("clients/acme", [])  # False
```

Deliberate. A misconfigured process that loses its allowlist fails closed, rather than
gaining the run of the drive.
