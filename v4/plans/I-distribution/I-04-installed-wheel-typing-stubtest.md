# I-04 — Installed-wheel typing check and stubtest

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-01](I-01-packaging-hardening.md), [B-10](../B-spike/B-10-ext-helpers-stub-workflow.md), [C-14](../C-butcher/C-14-pyi-stub-emitter.md), [C-27](../C-butcher/C-27-port-ext-helpers.md) |
| Blocks | [I-21](I-21-fresh-machine-install-rehearsal.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | yes (stub surface depends on D4/D11) |
| Decisions | D11, D16, D100, PD-23, 13 B10, 19 §8 |
| Sources | [08-build-release.md §5, §7.9, §7.11](../../research/08-build-release.md), [13-aiogram-rust-review.md B10](../../research/13-aiogram-rust-review.md), [02-butcher.md §5.1](../../research/02-butcher.md), [19 §8](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The public types are compiled pyclasses, so their whole typed surface lives in generated `.pyi` stubs. aiogram_rust's
stubs were missing 203 members until they were checked against the installed package (13 B10). Running mypy inside the
repo doesn't catch this, because mypy sees the source tree, not what the wheel ships. Three further problems need their
own checks:
- `inspect` rejects a `text_signature` containing `Default(...)`, so generated signatures use `...` while the stubs carry
  the real defaults (19 §8);
- the stubs are keyword-only (D100);
- the stubs have no `**extra` (PD-23).

## Scope

**In:**
- A typing suite `tests/typing/` of `assert_type` / `reveal_type` cases. It is run by mypy **from a temp dir outside the
  checkout** against the installed wheel (`python -P`, a venv without the repo on `sys.path`).
- `stubtest aiogram` against the installed wheel, with an allowlist file that must stay small and commented.
- `inspect.signature` smoke over every generated type, method and shortcut: no `ValueError`, keyword-only parameters,
  `...` for nonliteral defaults.
- A packaging assertion that every runtime pyclass has a stub entry, and every stub entry exists at runtime. This is the
  B10 "hand-written surface must reach the stubs" check, including `*_ext.pyi` fragments.

**Out:**
- Stub generation (C-14).
- `_ext.pyi` fragment merge mechanics (B-10 / C-27).
- Docs from stubs (I-09).

## Checklist

- [ ] `tests/typing/test_public_api.py` (type-check only): representative cases.
      - `Message` fields, including `from_user` from wire `from`.
      - Tuple collections (D106).
      - `Unknown…` union members.
      - `message.answer(text=...)` returning `Coroutine[..., Message]`.
      - `bot.send_message(chat_id=..., text=...)`.
      - `bot.call(..., returns=Message)`.
      - `obj.replace(...)` / `copy.replace`.
      - `to_json() -> bytes`, `model_dump_json() -> str`.
      - Positional-call **errors** (`# type: ignore[misc]` expected-error markers).
- [ ] CI job: install the wheel built by I-02 (or `maturin build` in PR CI), copy `tests/typing/` to `$RUNNER_TEMP`,
      run `mypy --strict` there with `--python-executable` set to the venv.
- [ ] `python -m mypy.stubtest aiogram --allowlist tests/typing/stubtest-allowlist.txt` on the installed wheel.
- [ ] `tests/test_packaging/test_signatures.py`: iterate over generated classes (from the generated re-export modules,
      C-13), call `inspect.signature`, assert every parameter is `KEYWORD_ONLY` (except `self`), and that no default
      repr contains `Default(`.
- [ ] Runtime ↔ stub parity test: names in `dir(aiogram.types.X)` (public) versus the names parsed from
      `aiogram/types/x.pyi` via `ast`.
- [ ] Tests (100% coverage of any helper code).
- [ ] No changelog fragment (internal); no registry entry.

## Acceptance criteria

- Typing suite, stubtest and the signature test all pass on cp311 and cp314 wheels.
- Deleting one member from a generated `.pyi` in a scratch commit makes both stubtest and the parity test fail.
- The stubtest allowlist has a comment per entry and no wildcard entries.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| PyO3 experimental stub generation | Experimental; we generate stubs from the IR | 02 §5.1 |
| Type-checking from inside the repo only | Doesn't see what the wheel ships | 13 B10 |
| `**extra` in stubs for D99 unknown kwargs | Unknown kwargs are runtime-only, documented | PD-23 |
| `Default(...)` in `text_signature` | `inspect` rejects it; stubs carry real defaults | 19 §8 |

## Validation

```bash
make dev
uv run pytest tests/test_packaging -q
uv run mypy aiogram
# CI: installed-wheel typing job and stubtest job (see Checklist)
cargo xtask butcher check
```

## Workflow notes

- Inputs: B-10 (fragment workflow), C-14 (stub emitter), I-01 (wheel contents).
- If B-13 is a no-go this plan is `blocked`: the stub surface is re-planned with the redesigned model layer.
- Runs in parallel with I-03 and I-09.

## Notes

(empty)
