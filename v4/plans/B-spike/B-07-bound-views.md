# B-07 — Bound views (D103)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-05](B-05-views-cache-gc-routing-keys.md), [B-06](B-06-value-semantics-native-api.md) |
| Blocks | [B-09](B-09-sendmessage-encoder-response.md), [B-11](B-11-cache-gc-teardown-ft-tests.md), [B-12](B-12-dispatch-harness.md), [H-13](../H-testing-observability/H-13-binding-identity-rewrite.md), [B-13](B-13-gate-run-and-decision.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md) |
| Gate-conditional | no |
| Decisions | D103, D53 (scope), R02, PD-03 |
| Sources | [19 D103](../../research/19-review-resolutions.md), [01-models.md §3.2](../../research/01-models.md), [codex-review.md R02](../../research/codex-review.md), [07-free-threading.md §5](../../research/07-free-threading.md), [14-testing.md D53](../../research/14-testing.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x re-mounts an update for another bot with a `model_dump` + `model_validate` round-trip that costs 179 µs
(`Dispatcher.feed_update` in `aiogram/dispatcher/dispatcher.py`). `BotContextController.as_`
(`aiogram/client/context_controller.py`) rebinds only the receiving object. D103 replaces both with
**independent bound views**:
- `obj.as_(bot)` returns a new view over the same immutable data;
- children of a view inherit its bot;
- nothing redirects another holder's shortcuts.

R02's acceptance test is a gate item (B-00).

## Scope

**In:**
- `as_(bot)` on every spike type: a new wrapper sharing `data` and `raw`, with an empty cache and the new bot. O(1)
  regardless of tree size.
- Children materialised from a view carry the view's bot. `obj.bot` returns the view's bot or `None`.
- Shortcuts capture the bot of their own view at call time. `message.answer` itself is B-09; here, a test-only
  `_core._bound_bot(obj)` hook or B-09's shortcut once merged.
- Remount helper for B-12: `update.as_(bot)` is the dispatcher remount.
- The R02 acceptance tests and the 07 §5 contention test (cp314t).

**Out:**
- Cross-view identity: not promised (D103).
- The migration-checker rule for a bare `x.as_(bot)` statement (I-17).
- The testing-toolkit identity rewrite (H-13).

## Checklist

- [ ] `as_(bot)` returning a new view; children inherit the view's bot.
- [ ] A test that `update.as_(b2)` doesn't change `update.bot`, `update.message.bot` or any child materialised
  before the call (R02 "before and after child materialisation").
- [ ] A concurrency test on cp314t: two threads take `as_(b1)` / `as_(b2)` of one decoded payload and read
  `.message.chat.bot` 10k times each; every read returns its own view's bot.
- [ ] A test that `Update(message=m)` with a bound `m` follows the B-06 seeding rule.
- [ ] Register the re-mount workload (plain-text and realistic update) in the B-02 adapter, to check the B-00 O(1)
  floor.
- [ ] Tests in `tests/test_core/` (100% of new Python).
- [ ] No changelog or registry entry here (not wired, PD-03). Breaking change 22 (`as_` returns a new view) is
  registered by I-17 / C-18; name it in Notes.

## Acceptance criteria

- `m2 = m.as_(b2)`: `m.bot is b1`, `m2.bot is b2`, `m2.chat.bot is b2`, `m.chat.bot is b1`, and `m2 == m` (D108).
- The cp314t contention test passes with no cross-view read.
- Re-mount time differs by less than 10% between the plain-text and the realistic update (O(1)).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A shared mutable `Ctx` per tree (`ArcSwapOption`) | Hidden mutation across aliases; one holder redirects another's shortcuts | D103 (replaces 01 §3.2 Ctx) |
| Per-wrapper rebinding in place (3.x `as_`) | Parent and child disagree; not safe across loops | R02 |
| The JSON round-trip re-mount | 179 µs | 01 §1 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests/test_core
uv run mypy aiogram
```

On cp314t: `PYTHON_GIL=0 uv run pytest tests/test_core -k bound`.

## Workflow notes

- Inputs: B-05 views; the B-06 seeding rule.
- Outputs: the binding contract for H-13 (the fake builds updates already bound) and E-14 (remount); the remount
  path for B-12.

## Notes
