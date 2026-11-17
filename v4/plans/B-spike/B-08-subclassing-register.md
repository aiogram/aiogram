# B-08 — Subclassing + `register`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-05](B-05-views-cache-gc-routing-keys.md), [B-06](B-06-value-semantics-native-api.md) |
| Blocks | [B-11](B-11-cache-gc-teardown-ft-tests.md), [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | D83, D84, D108 (pickle), 01 §3.5, PD-03 |
| Sources | [01-models.md §3.5, §3.6, §5](../../research/01-models.md), [02-butcher.md §5.1](../../research/02-butcher.md), [13-aiogram-rust-review.md §6](../../research/13-aiogram-rust-review.md), [codex-review.md R03, R05](../../research/codex-review.md), [19 R03](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Users subclass types to add methods, and must be able to make the decoder produce their subclass:
`register(Message, MyMessage)` (01 §3.5, breaking change 3). 02 §5.1 says D11 "removes the subclass-instantiation
risk from the spike", but that holds only for the default path (one class per type). A **registered** Python
subclass still has to be instantiated by the Rust decoder, and that is an open PyO3 mechanics question. In 3.x the
type hierarchy also has real bases (`Message(MaybeInaccessibleMessage)`, `MessageOriginUser(MessageOrigin)`), and
secondary bases go through ABC registration (D83).

## Scope

**In:**
- **Class hierarchy.** A pyclass base `TelegramObject` (`subclass`) carrying the shared surface from B-06. Bot API
  bases as real pyclass parents (`extends`): `MaybeInaccessibleMessage` → `Message` / `InaccessibleMessage`,
  `MessageOrigin` → its four variants. Every pyclass is `subclass` + `frozen`.
- **Secondary bases (D83).** The ABC `register` mechanism, shown with a test-only secondary base, since no spike
  type has a real one (the 3.x `MutableTelegramObject` base goes away under D15).
- **Registry.** `_core.register(base, sub)`, which lives in `_core`, **not** in `aiogram.types` (PD-03).
  - It validates that `sub` is a Python subclass of `base`.
  - It is a process-global, free-threading-safe registry read by wrapper materialisation and the
    `from_json` / `from_dict` / constructor paths.
  - The default (unregistered) path costs one relaxed atomic load at most.
- **Instantiation of a registered subtype from Rust.**
  - It must create an instance of the Python subtype carrying the same Rust payload, **without** running the
    user's `__init__`.
  - User state after decode: `__dict__` empty.
- **Semantics.** Equality is class-strict: `MyMessage` never equals `Message` with the same data (D84). Pickle keeps
  the subclass, and its `__dict__` state, per the B-06 decision.
- **Benchmarks.** Registered-subclass instantiation (informational, 01 §5.2), plus a check that the default path
  isn't slower with a registry entry for another type.

**Out:**
- `aiogram.types.register` as a public wired API (C-18 / I-17).
- Secondary-base emission from the overlay (C-06 / C-18).
- Subclassing of generated **method** classes: not supported (D96).

## Checklist

- [ ] Base `TelegramObject` pyclass plus `extends` hierarchies; `isinstance` / `issubclass` match 3.x for every
  spike type, checked against the 3.x class hierarchy in `aiogram/types/*.py`.
- [ ] D83 ABC `register` for a test-only secondary base.
- [ ] Decide how a registered Python subtype is instantiated from Rust (proposed default: allocate through the
  subtype's `tp_alloc` via PyO3's initializer-into-subtype path, whichever public or `unsafe` API pyo3 0.30 offers
  for creating an object of a given subtype. Never call `sub(...)`, which runs user `__new__` / `__init__` and
  kwargs validation. If pyo3 has no sound API, stop and record it under Notes as a gate risk). Record in Notes and
  flag to owner.
- [ ] Decide `register` after decoding has started, on a free-threaded build (proposed default: allowed. Copy-on-write
  registry with atomic publish; wrappers already materialised keep their class; new materialisations see the new
  entry. Documented, no lock on read). Record and flag.
- [ ] `_core.register` with validation (non-subclass → `TypeError`; registering twice replaces with a
  `RuntimeWarning`).
- [ ] Equality class-strictness and pickle round-trip of a registered subclass.
- [ ] Register the subclass-instantiation workload and the "default path with registry populated" workload in B-02.
- [ ] Tests in `tests/test_core/`:
  - decoded `update.message` is `MyMessage` after register, and `Message` before;
  - user `__init__` not called;
  - subclass methods / properties work;
  - `MyMessage(...) != Message(...)` with the same data;
  - pickle keeps the class;
  - a concurrent `register` + decode smoke on cp314t (100% of new Python).
- [ ] No changelog or registry entry here (not wired, PD-03). Breaking change 3 is registered by I-17 / C-18; name it
  in Notes.

## Acceptance criteria

- After `_core.register(Message, MyMessage)`, `type(_core.decode_update(raw).message) is MyMessage`, and an
  `__init__` that raises is never triggered.
- Default-path first access with an unrelated registry entry is within noise (≤2%) of the empty-registry run (B-02
  workload).
- `isinstance(origin, MessageOrigin)` and `isinstance(msg, MaybeInaccessibleMessage)` hold, and the test-only
  secondary base passes `isinstance` through ABC `register`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A Python facade class per type | One class per type that the decoder creates directly | D11, 02 §5.1 |
| Instantiating a registered subclass by calling it | Runs user `__init__` / validation on every decode | 01 §3.5 |
| Multiple inheritance via PyO3 | PyO3 has single inheritance; secondary bases go through ABC `register` | D83, 13 §6 |
| Subclasses equal to base instances with the same data | Same class + data | D84 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests/test_core
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: B-05 views; B-06 shared surface and pickle decision.
- Outputs: the class-hierarchy and registry design for C-18 (emitted `extends`, secondary bases) and I-17 (checker
  rules for subclass users).
- Can run in parallel with B-09, B-10 and B-11.

## Notes
