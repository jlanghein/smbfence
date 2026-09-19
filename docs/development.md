# Development

```bash
git clone git@github.com:jlanghein/smbfence.git
cd smbfence
uv sync --extra dev
```

## The verify loop

Run all four before every commit. CI runs the same four.

```bash
uv run --extra dev ruff format .
uv run --extra dev ruff check --fix .
uv run --extra dev ty check src
uv run --extra dev pytest
```

!!! warning "`uv run`, not `uvx`"
    `uvx` pins nothing. It resolves the newest release on every invocation, so the checks
    can change behaviour with nothing in the repository changing — a formatter minor
    release starts reformatting something it previously ignored, and CI fails on a commit
    that touched none of it.

    `ruff` and `ty` are declared in the `dev` extra so the lockfile pins both.

## Conventions

The binding rules are in [`AGENTS.md`](https://github.com/jlanghein/smbfence/blob/main/AGENTS.md).
The short version:

- **Comments explain *why*, never *what*.** If a name or signature already said it, delete
  the comment. `API_TIMEOUT_SECONDS = 30`, not `timeout = 30  # seconds`.
- **Catch specific exceptions.** Never bare `except:` or `except Exception:` unless
  re-raising.
- **No suppressions as a first resort.** `# noqa` and `# type: ignore` mean the code is
  wrong, not the tool. If it really is a false positive, document why.
- **Types at module boundaries**, always.
- **Small, focused commits**, one concern each, never breaking the loop.

## Documentation

```bash
uv sync --extra docs
uv run --extra docs mkdocs serve
```

The API reference is generated from docstrings by `mkdocstrings`, so documenting a
function means writing its docstring — there is no second copy to fall out of date.

## Adding a dependency

There are three at runtime: `smbprotocol`, `pydantic`, `pydantic-settings`. A fourth
needs a reason in the commit message. A library that guards access to a file share should
be cheap to audit.
