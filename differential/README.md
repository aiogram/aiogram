# Differential harness

Runs the same probes against two aiogram installs and compares the results case by case. The
oracle for aiogram 4.0 is an external, pinned 3.x venv (PD-12); the same harness checks 3.x
against a patched 3.x. Plan: `v4/plans/A-contracts/A-07-differential-framework.md`.

Dev tooling only: `differential/` is excluded from the sdist and wheel, and nothing in `aiogram`
imports it.

## CLI

```bash
uv run python -m differential run --kind smoke --left git:HEAD --right path:.
uv run python -m differential run --kind smoke --left 'pypi:aiogram<4' --right path:. --poison right
uv run python -m differential run --kind model --left pypi:aiogram==3.32.0 --right path:. \
    [--manifest FILE] [--corpus DIR] [--max-diffs N]
```

- `--kind`: `smoke | model | request | routing`. Only `smoke` has a probe so far; A-08 (model), A-09
  (request) and A-10 (routing) add theirs as `sides/aiogram3/<kind>.py`.
- A side is `pypi:<requirement>`, `git:<ref>` or `path:<dir>`.
- `--manifest` defaults to `differential/manifests/<kind>.toml`; `--corpus` to `benchmarks/corpus`.

| Exit | Meaning |
|---|---|
| 0 | no unapproved mismatch |
| 1 | unapproved mismatches; with `--poison`, the expected result |
| 2 | `--poison` given and nothing differed: `poison not detected`, the harness is blind |
| 3 | harness error: bad arguments, side or manifest, venv build, side crash, malformed trace |

## Concepts

**Sides and venvs.** Each side gets its own venv under `.differential/venvs/<hash>` (gitignored),
created with `uv venv` on the runner's interpreter plus `uv pip install`.
- `pypi:` and `git:` venvs are built once and reused. Delete `.differential/` to pick up a newer
  release for `pypi:aiogram<4`.
- `git:<ref>` is exported with `git archive` into `.differential/src/<sha>` and installed from there.
  The plan says `git worktree`; the archive gives the same clean tree of the ref without worktree
  bookkeeping.
- `path:<dir>` is rebuilt on every run, since its content changes.

**Side scripts** live in `sides/<adapter>/<kind>.py`. The adapter is picked from the side's
`aiogram.__version__`: `aiogram3` for 3.x, `aiogram4` for 4.x, which the B/D/E plans add. A side
script is standalone: stdlib plus aiogram only. It runs as
`python -I <script> --corpus DIR --out FILE --trace-module differential/trace.py --header JSON [--poison]`.
`-I` keeps the repository off its `sys.path`. The one shared file, `trace.py`, is stdlib-only and
loaded by explicit path, so both sides use the same encoder.

Probes go through the public entry points (`Update.model_validate_json`, `bot(method)`,
`feed_update`, ...), not internals.

**Trace** (`trace.py`). JSONL, written with `trace.dumps`: sorted keys and no whitespace.
- Line 1 is `{"__header__": {side, adapter, aiogram, commit, python, implementation, platform, kind,
  poison}}`. It is printed in the report and never compared.
- Every other line is one record:
  `{case, probe, ok, value | error: {type, attrs}, meta}`. A failing probe is recorded, not raised.
  `attrs` must be stable across dependency versions (the two venvs resolve independently): for a
  pydantic `ValidationError`, record `errors(include_url=False, include_input=False)`, not `str(exc)`.
- `trace.canonical` makes values JSON-native. Finite floats stay numbers. Anything else that JSON
  cannot hold exactly gets a `__kind__` tag: `float` (nan/inf), `bytes` (base64), `set` (sorted
  items), `tuple`, `datetime`/`date`/`time`/`timedelta`, `decimal`, `enum`, `dict` (non-str keys, or
  a literal `__kind__` key), and `repr` (anything else).
- Comparison is on the canonical string, so `True` never equals `1`. `meta` (timings, platform) is
  left out of equality; only a comparator may look at it.

**Manifest** (`manifests/<kind>.toml`; any path works with `--manifest`):

```toml
[[case]]
match = "model.update.realistic.*/dump"  # fnmatch, case-sensitive, over "<case>/<probe>"
class = "approved"                       # invariant | approved | new
decision = "D86"                         # required for approved / new; plan ids (3x-09) for 3.x vs 3.x
assert = "wire_names_in_dump_json"       # approved only: a comparator registered in runner.py
gate = true                              # the decision is gate-dependent (D104); default false
when = "aiogram4"                        # optional: active only if a side uses this adapter
note = "free text"
```

Entries are tried in file order and the first active match wins, so keep case-specific entries
above probe wildcards (`model.*/dump_json`). A record that matches nothing is
`invariant`. The loader rejects unknown keys, so a plan that needs a new key (for example
normalisation rules or platform conditions) adds it to the loader and the self-tests.

**Classes:**
- `invariant`: `ok`, `value` and `error` are exactly equal.
- `approved`: the named comparator's narrow assertion must hold, and the rest of the record must
  still be equal.
- `new`: the left side failed and the right side succeeded.

A case present on one side only is always a mismatch.

**Poison control.** `--poison left|right` passes `--poison` to that side only. The side script then
corrupts real behaviour in its own process; `smoke` flips one field of every decoded object. The run
must report at least one mismatch per kind, or it exits 2 with `poison not detected`. CI
(`.github/workflows/differential.yml`: weekly, on demand, and on PRs that touch `differential/`,
the corpus or the workflow) runs `smoke` once clean and once
poisoned; a plan that adds a kind's probe adds the same two steps for that kind.

## Adding an approved difference

1. Write the comparator in `runner.py`. It takes `(left, right)` records and returns them with the
   approved difference removed, or raises `Mismatch("why")` when the difference is not the approved
   one:

   ```python
   @comparator("wire_names_in_dump_json")
   def wire_names_in_dump_json(left: Record, right: Record) -> tuple[Record, Record]:
       if right["value"] != rename_to_wire(left["value"]):
           raise Mismatch("right is not left with wire names")
       return left, {**right, "value": left["value"]}
   ```

   Keep the assertion narrow: it states exactly what differs, and everything else is still compared.
   Each seeded 4.0 stub (`_stub(...)` in `runner.py`) never approves; replace it with the real
   comparator.
2. Add or refine the `[[case]]` entry in the kind's manifest: a `match` as narrow as the cases it
   covers, the `decision` id and the `assert` name.
3. Cover the comparator in `tests/test_differential_framework.py`, both when it holds and when it
   does not.

The seeded entries carry `when = "aiogram4"`, so they stay inert in 3.x-vs-3.x runs. Their `match`
patterns are placeholders for A-08..A-10 and the 4.0 plans to refine. `gate = true` entries are void
if B-13 is a no-go.

## Self-tests

`uv run pytest tests/test_differential_framework.py`: fake in-process sides, no venvs or network.
They cover the trace encoding, each comparator, manifest matching and validation, the poison
self-check, and the smoke side run in-process.

## Model kind

`sides/aiogram3/model.py` (A-08) records what 3.x models do; a 4.0 adapter implements the same
cases and probe names. Bots carry fabricated tokens and send nothing.

- `model.<input id>`, for every corpus input of kind `update`: `decode.json`
  (`Update.model_validate_json` with a bot in the context), `decode.dict` (`json.loads` +
  `model_validate`, the webhook path), `dump.python`, `dump.wire` (`model_dump(mode="json",
  exclude_unset=True)`, without and with `by_alias`), `dump_json.default` (`{type, value: model_dump_json(),
  wire: model_dump_json(by_alias=True, exclude_unset=True)}`), `event`, `access` (the paths in
  `manifests/model.access.toml`, which needs a list for every new update input), `extra`
  (`model_extra` of the root and of nested objects that have extras), `eq.same_bot`, `eq.same_token`,
  `eq.other_bot`, `hash` / `hash.event` (the class of `hash()`, never its salted value),
  `pickle.unbound`, `pickle.bound`, `copy.valid`, `copy.invalid` (`model_copy(update=...)`). When
  `decode.json` fails, the later probes are recorded as `DecodeFailed`, so both sides emit the same keys.
- `model.construct.<type>`: `dump.python` (Python mode, keeps `Default(...)` placeholders) and
  `dump.wire` of constructor kwargs; `Message.wire_kwargs` passes `from`; `User/extra.non_json`.
- `model.mutate.<type>/mutate`: attribute assignment.
- `model.codex11.<name>/observe`: the model probes of `v4/research/codex-review.md` section 11.

ValidationError attrs are `error_count` plus each error's `type` and `loc`: no messages. `--poison`
drops the first key of every `dump.*` value.
