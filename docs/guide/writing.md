# Atomic writes

## An interrupted write leaves something that looks finished

Write straight to the final name and a link dropping mid-transfer leaves a **truncated
file under the name a whole one was expected at**.

It gets worse on the retry. The retry reads the file back, finds bytes that differ from
what it meant to write, concludes somebody else owns it, and refuses. For good. The
failure is permanent and the cause is invisible.

## Written beside itself, then renamed

```python
share.write_file("clients/acme/out/invoice.pdf", pdf_bytes)
```

Internally:

```
1. write  → clients/acme/out/invoice.pdf.partial
2. rename → clients/acme/out/invoice.pdf
```

A transfer that stops half way leaves a `.partial` file and nothing under the final name.
The next run writes it again.

## A retry of a completed write is success

```python
share.write_file(path, content)  # writes
share.write_file(path, content)  # identical bytes already there — returns quietly
```

Idempotent by design. A scheduled publisher that cannot tell whether last night's run
finished should be able to simply run again.

## A conflicting file is never overwritten

```python
share.write_file(path, b"mine")  # ConflictingContentError
```

A file under the same name holding **different** bytes belongs to somebody else, and is
left exactly where it is.

!!! danger "The one unrecoverable operation"
    Everything else this library does can be retried or undone. Overwriting somebody
    else's document on a shared drive cannot — there is no version history on an SMB
    share, and the owner may not notice for months. So it does not do it, and raises
    instead.

## Writes are guarded too

The allowlist applies identically to writes:

```python
share.write_file("clients/other/invoice.pdf", b"x")  # PathNotAllowedError
```

Reading the wrong folder is an error. Writing to it is somebody else's problem forever.
