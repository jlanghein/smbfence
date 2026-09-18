# Development Conventions

The binding conventions for this repository. Every rule here is enforced by the verify
loop or by CI, not left to taste.

## Philosophy

- **Simplicity is king** — the simplest solution that works is the best solution
- **Self-documenting code** — if it needs comments, refactor it
- **Functional over OOP** — pure functions, composition, immutability
- **Commit early, commit often** — small, focused, verified commits
- **No shortcuts on quality** — fix errors properly, never suppress warnings without fixing the root cause

---

## Cross-Language Design Principles

### Code Design
- Prefer **pure functions** where feasible; isolate side effects.
- Avoid hidden state and mutable globals.

### Types & Data
- Declare types explicitly at *module boundaries*.
- Model domain constraints with `Literal`, `TypedDict`, Pydantic models.

### Error Handling
- Treat errors as structured data, not control flow.
- **Catch specific exceptions**, never bare `except:` or `except Exception:` unless re-raising.
- Add contextual information when propagating errors.
- Let unexpected errors crash — they reveal bugs. Only catch what you can handle.

### Resource Management
- **Always use context managers** (`with`) for resources needing cleanup.
- Never manually call `.close()`.

### Testing
- **Unit tests** for pure logic, **integration tests** for I/O boundaries.
- Assert behavior, not implementation details.
- Use **AAA** (Arrange, Act, Assert).

### Snapshot Testing with inline-snapshot

Freeze expected values directly in test files. Start with empty `snapshot()` and let
the tool fill them in.

```bash
uv run --extra dev pytest --inline-snapshot=create   # fill empty snapshot() calls
uv run --extra dev pytest --inline-snapshot=fix      # update when data changes intentionally
```

```python
from inline_snapshot import snapshot
from dirty_equals import IsInt, IsDatetime


def test_engagement():
    result = build_engagement(name="test")

    assert result.dict() == snapshot(
        {
            "id": IsInt(),           # dynamic values via dirty-equals, preserved on --fix
            "name": "test",
            "created_at": IsDatetime(),
        }
    )
```

- Start with empty `snapshot()`, never hand-write expected values
- Convert data to builtins before snapshotting
- Review `git diff` before committing updated snapshots

### Comments & Docs
- **Write the implementation in English** — code, identifiers, comments, docstrings,
  tests and commit messages. A German-facing product is not a German codebase.
- Comments explain *why*, never *what*.
- Bad: `timeout = 30  # API timeout in seconds`
- Good: `API_TIMEOUT_SECONDS = 30`
- If code needs lots of comments, **refactor** instead.

### ASCII Diagrams & Tables
- All lines within a box must have identical visual width.
- Markdown tables should have aligned columns.

### Architecture & Boundaries
- Divide code into layers (core logic, side effects, interfaces).
- Keep modules small and focused.

---

## Layered Architecture

**1. Dependencies flow one direction.** If A → B → C, then C can import B and A, but A
cannot import C. This alone eliminates circular imports.

**2. Leaf modules are the foundation.** Modules with zero internal imports are the most
stable — shared types, constants, pure data structures.

**3. Group by reason to change.** Same reason to change = same module.

**4. Configuration sits low.** Readable by all layers, depends on nothing.

**5. Ports and adapters emerge naturally.** Core (pure, no I/O) doesn't know how it's
called or what it calls.

**6. Comments signal missing structure.** Section dividers usually mean the file does
too much.

**7. Name layers by role, not technology.** `services/` not `openai/`.

---

## Python

### Tools
| Tool | Purpose | Install |
|------|---------|---------|
| `uv` | Package/project manager | `brew install uv` |
| `ruff` | Linter & formatter | declared in `[project.optional-dependencies] dev` |
| `ty` | Type checker (Astral) | same |
| `pytest` | Testing | same |

### Before Commit

```bash
uv run --extra dev ruff format .
uv run --extra dev ruff check --fix .
uv run --extra dev ty check .
uv run --extra dev pytest
```

**Run the tools through `uv run`, not `uvx` — `uvx` pins nothing.** It resolves the
newest release every invocation, so the loop can change behaviour with nothing in the
repository changing. This has already bitten the other projects: `uvx ruff` resolved to
0.16.2 against a lock at 0.15.9, and 0.16 began formatting Python snippets inside
markdown, so `uvx ruff format --check .` reported `AGENTS.md` itself as unformatted.
(Carried over from `../windee/CLAUDE.md`, which supersedes raven's `uvx`-based loop.)

**Pre-commit checklist** (all must pass):
- [ ] `ruff format .` — no files reformatted
- [ ] `ruff check .` — no errors
- [ ] `ty check .` — all checks passed
- [ ] `pytest` — all tests passed
- [ ] No obvious comments, no section divider comments (`# ====...`)
- [ ] Comments explain *why*, not *what*

### No Suppressing Errors

- Do NOT add `# noqa`, `# type: ignore` or similar as a first resort
- Do NOT add rules to `ignore` lists to bypass errors
- If a tool reports an error, **fix the code** — the tool is usually right
- If it is genuinely a false positive, document *why* in a comment

```python
# BAD: Suppressing instead of fixing
conn.execute(f"SELECT * FROM {table}")  # noqa: S608

# GOOD: Validate input to prevent injection
safe_table = _validate_identifier(table)
conn.execute(f"SELECT * FROM {safe_table}")
```

### Style

```python
def is_within(path: str, allowed: Sequence[str]) -> bool:
    """Whether a path sits inside one of the allowed roots."""
    candidate = normalise(path)
    return any(
        candidate == normalise(root) or candidate.startswith(normalise(root) + SEPARATOR)
        for root in allowed
    )
```

- Type annotations: always, Python 3.13+ (`list[T]`, `X | None`)
- Docstrings: brief, public APIs only
- Async for I/O

### Dependencies

Three at runtime: `smbprotocol`, `pydantic`, `pydantic-settings`. Adding a fourth needs a
reason in the commit message. A library that guards access to a file share should be
cheap to audit.

---

## Secrets

Share credentials come from the environment or a gitignored `secrets.env`, never from a
tracked file and never from a default in code. `ShareConfig` holds the password as a
Pydantic `SecretStr` so it cannot be logged by accident.

---

## Git

### Commit Early, Commit Often
- **Small, focused commits** — each does one thing
- **Commit before refactoring** — a checkpoint to roll back to
- **Never commit broken code** — all commits pass the verification loop

### Commit Format
```
type: short description
```

| Type | Use |
|------|-----|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `chore:` | Maintenance |
| `refactor:` | Restructure (no behavior change) |
| `test:` | Tests |

### Pull Requests
- **Language**: English, like the code and the commits
- **Title**: same format as commits
- **Description**: explain the *why*, not just the *what*
- Link related issues. One logical change per PR.

---

## Quick Reference

| Lang | Format | Lint | Type Check | Test |
|------|--------|------|------------|------|
| Python | `ruff format .` | `ruff check --fix .` | `ty check .` | `pytest` |

**The Loop:** Change → Verify → Commit → Repeat

If it's not tested, it's not done.
