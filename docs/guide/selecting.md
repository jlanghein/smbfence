# Selecting entries

## A hand-filed share is full of things nobody filed

Filed by hand from both Windows and macOS, a share accumulates metadata in every folder:

| From | Files |
|---|---|
| macOS | `.DS_Store`, `._`-prefixed resource forks, `.Spotlight-V100`, `.Trashes` |
| Windows | `Thumbs.db`, `desktop.ini` |

They sit beside the real files and they are never what a caller asked for.

```python
from smbfence.names import is_noise

is_noise("._STA_2026.sta")  # True — an AppleDouble resource fork
is_noise("Thumbs.db")  # True
is_noise("STA_2026.sta")  # False
```

## Suffix and prefix are different questions

This is the subtle one.

Selecting *by* suffix and *excluding* by prefix are separate tests, and folding them into
one lets an excluded file through the moment a caller asks by suffix alone.

```python
from smbfence.names import select

listing = [
    "STA_12345_20260101_120000.sta",  # a booked export
    "VMK_12345_20260101_120000.sta",  # a provisional one — same extension
    "._STA_12345_20260101_120000.sta",
    ".DS_Store",
    "notes.txt",
]

select(listing, suffix=".sta", excluded_prefixes=["VMK_"])
# ["STA_12345_20260101_120000.sta"]
```

!!! danger "Where this costs money"
    Banking exports are the usual case: a booked statement and a provisional one
    (*Vormerkung*) under the same `.sta` extension. Importing the provisional file
    records money that has not moved. Exclusions are applied **before** the suffix test,
    never merged with it, so a caller asking only by suffix still does not receive one.

## Results are sorted

```python
select(["b.sta", "a.sta", "c.sta"], suffix=".sta")
# ["a.sta", "b.sta", "c.sta"]
```

A directory listing arrives in whatever order the server chose. Without sorting, a caller
that processes files in listing order behaves differently against two servers holding
identical files — which is the kind of difference that only shows up in production.
