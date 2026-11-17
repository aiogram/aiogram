# H-13 — Binding and identity rewrite (bound views)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-12](H-12-toolkit-model-api-migration.md), [B-05](../B-spike/B-05-views-cache-gc-routing-keys.md), [B-07](../B-spike/B-07-bound-views.md), [B-13](../B-spike/B-13-gate-run-and-decision.md) |
| Blocks | [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | yes |
| Decisions | D53, D103, D108, D104, R02 |
| Sources | [14-testing.md D53, §3 "Rewritten"](../../research/14-testing.md), [01-models.md §3.1–3.2](../../research/01-models.md), [19 D103, D104, D108](../../research/19-review-resolutions.md), [codex-review.md R02](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The toolkit promises that inside a handler `message is chat.messages[-1]`. Today `aiogram/test/mounting.py`
(316 lines) re-mounts results to the bot. `FakeTelegramSession.make_request` returns `mount(result, bot)`.

In 4.0 the model is different:
- `as_(bot)` returns a **new independent view** (D103);
- identity holds only **within one view** and for unbound construction, through cache seeding (D53);
- the dispatcher creates a new root view when remounting.

So the world must build objects **already bound** to the receiving bot, and the dispatcher must never remount them.
R02 warns that the fake's identity promise must not dictate production ownership.

## Scope

**In:**
- Rewrite `mounting.py`: the world constructs updates and results bound to the receiving bot at creation, using
  B-07's construction-with-bot API. Constructor cache seeding (B-05) keeps `Update(message=m).message is m`.
- `FakeTelegramSession.make_request` returns the world-owned bound object. There is no `as_()` on the return path.
- Feed path: updates are passed to the dispatcher already bound to the target bot, so no remount happens. The test
  asserts the dispatcher's no-remount fast path is taken.
- Remove `plugin._differ_only_in_binding` / `_describe_binding`, because D108 equality ignores the binding. Adjust
  `pytest_assertrepr_compare` accordingly.
- Replace the remaining `as_(` uses (5) with views captured from the world.

**Out:**
- Production binding semantics (B-07).
- Runner delivery (H-14).

## Checklist

- [ ] New `mounting.py`, or delete it if bound construction makes it trivial. Prefer deletion.
- [ ] Session return path and world storage use bound views.
- [ ] **Decide per-receiving-bot identity** (proposed default: the promise is "`message is chat.messages[-1]` for
      the bot that received the update". In a multi-bot world, the world keeps one bound view per (object,
      receiving bot), and identity across bots is not promised (D103). Document it in `testing.rst`). Record the
      decision in *Notes* and flag it to the owner.
- [ ] Tests:
  - [ ] the identity promise inside a handler (message, chat, reply);
  - [ ] a two-bot world where both bots see one group message: each handler sees its own bot's view and shortcuts
        go through the right bot (the R02 acceptance case);
  - [ ] the no-remount path;
  - [ ] assertion repr without binding noise.
- [ ] Update `tests/test_testing/test_mounting.py` (or remove it with the module).
- [ ] No changelog unless toolkit public behaviour changes. A documented identity scope change counts: add a
      fragment.

## Acceptance criteria

- `message is env.chat(...).messages[-1]` holds inside handlers for the receiving bot (test).
- In a two-bot world, shortcuts called from each bot's handler hit that bot's fake session (call log per bot).
- No `as_(` call remains on the toolkit's hot paths (grep guard), and the dispatcher's remount counter stays at 0
  for toolkit-fed updates.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A shared mutable tree binding so one object serves every bot | Cross-alias mutation; bindings redirect each other | D103, R02 |
| Keeping `mount()` re-binding on every result | `as_()` returns a new view, so identity with world state would break | D103 |
| Identity across `as_()` | Not promised by the model layer | D103 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Gate-conditional: the mechanism depends on B (D104). If B-13 is a no-go, this plan is re-planned with the new
  model layer.
- Inputs: B-05 (wrapper cache, seeding), B-07 (bound views, construction with bot).
- B owns the production identity tests. This plan only consumes them.

## Notes
