# E-14 — Feed paths (`runner.feed` / `runner.process`, `dp.feed_update`) and forward-compatible dispatch

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-13](E-13-runner-lifecycle-bot-registry.md), [E-11](E-11-error-model-bubbling.md), [E-05](E-05-typed-observers-unknown-update.md), [D-09](../D-client/D-09-response-decoder.md), [B-07](../B-spike/B-07-bound-views.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [E-12](E-12-runtime-errors.md) |
| Blocks | [E-15](E-15-poller.md), [E-16](E-16-webhook-core-aiohttp-sources.md), [E-17](E-17-asgi-app.md), [E-21](E-21-e-exit-gate.md), [G-02](../G-features/G-02-depends-scope-teardown.md), [G-06](../G-features/G-06-lazy-text-capture.md), [H-14](../H-testing-observability/H-14-delivery-through-runner.md) |
| Gate-conditional | partial — the O(1) remount via `update.as_(bot)` assumes D103 bound views (B-07); the rest is gate-independent |
| Decisions | R12, D10, D49, D103, D112, PD-04, PD-29, README breaking change 9 |
| Sources | [12-runtime.md §3, §7](../../research/12-runtime.md), [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md), [19 R12, R13, D103, D112](../../research/19-review-resolutions.md), [codex-review R12, R13](../../research/codex-review.md), [11-removals.md §1](../../research/11-removals.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

R12: each source must know what awaiting a feed call guarantees. 19 fixes the API: `runner.feed()` **admits** (awaits
capacity, then schedules); `runner.process()` runs inline and returns the reply (webhook). 10 §3: undecodable and
unknown-type updates go to `router.unknown_update`, and decode failures are also reported to `errors` with
`phase=DECODE`. 3.x re-mounts a foreign-bot update by a `model_dump`/`model_validate` round trip in
`Dispatcher.feed_update`; D103 makes it an O(1) new bound view.

## Scope

**In:**
- `runner.feed(bot, raw: bytes | Update) -> None`: decode in the core if bytes (D-09 `decode_update`; failures become
  the Update shell with `decode_error`), await admission capacity, schedule processing as a tracked task. Returning
  means admitted, not completed.
- `runner.process(bot, raw) -> TelegramMethod | None`: decode, run inline under the same concurrency accounting,
  return the handler's reply method (for webhook inline replies).
- **Handler-returned methods (PD-07):** a returned `TelegramMethod` is captured at handler return, inside the
  middleware scope, by E-02's handler-result seam (G-06 installs D-10's capture there). The feed path never captures
  after the outer chain has unwound: it receives the already-captured call and either returns it as the reply
  (`runner.process`) or executes it as a silent call (`runner.feed`, `phase=SILENT_CALL`). A failing silent call — including a `RetryMiddleware` give-up (G-13
  only re-raises, with `.attempts`) — is reported by this path through E-12's `emit_runtime_error` and never fails
  other updates.
- Processing completes only after the E-11 `close_point` (Depends teardown, PD-04) has run; the task is counted
  in-flight until then.
- `Dispatcher.feed_update(bot, update, **kw)` / `feed_raw_update`: routing only, unchanged signatures; without a Runner
  they use the E-03 epoch cache. Remount: `if update.bot is not bot: update = update.as_(bot)` (D103).
- **Forward-compatible dispatch:** `Update.event_type` returns unknown keys (C-19 / B decode); the routing stage sends
  unknown-type updates and decode shells to `unknown_update`; `dp.update` outer middlewares still see them (UserContext
  / FSM middlewares must tolerate an event with no user/chat). Unhandled → logged once per type and dropped.
- `DecodePolicy` (`"lenient"` default / `"strict"`) honoured on the feed path.
- Per-update error isolation: an exception from one update never affects another task.

**Out:**
- Webhook `max_pending` / 5xx and reply encoding (E-16); Poller offset handling (E-15).
- Rust decode itself (D-09, B-03, B-14, C-19).

## Checklist

- [ ] `feed` (admission semantics) and `process` (inline + reply) on `Runner`.
- [ ] In-flight accounting includes `close_point`.
- [ ] Use the call already captured at E-02's handler-result seam (no capture in `feed` / `process`); silent-call
  failures (incl. Retry give-up) → E-12 `emit_runtime_error` with E-11's `phase=SILENT_CALL`.
- [ ] `dp.feed_update` remount via `as_()`; `feed_raw_update` decodes via the core.
- [ ] Unknown-type and shell routing into `unknown_update`; outer middlewares tolerate shells.
- [ ] Decide what event object `unknown_update` handlers receive (10 §3 Layer 1 says `UnknownEvent(type, raw)`,
  Layer 2 says the `Update` shell) (proposed default: always `UnknownEvent` with `type`, `raw`, and
  `decode_error: UpdateDecodeError | None`; `event_update` in data is the `Update`/shell) — record in Notes and flag to
  owner.
- [ ] Decide the order of `errors(phase=DECODE)` and `unknown_update` and the rule when either fails (R13)
  (proposed default: `unknown_update` routing first; then exactly one `errors` notification with `phase=DECODE` whose
  return value is ignored; an exception in an `unknown_update` handler follows normal E-11 bubbling with
  `phase=HANDLER`; the update completes once) — record in Notes and flag to owner.
- [ ] Decide `DecodePolicy` precedence (proposed default: `Dispatcher` policy governs update decoding on every feed
  path, `Bot` policy governs method responses; strict mode on the feed path raises `ClientDecodeError` (PD-29) into
  `errors(phase=DECODE)` instead of routing to `unknown_update`; sources still advance/acknowledge per E-15/E-16) —
  record in Notes and flag to owner.
- [ ] Decide the fate of user `@dp.update()` handlers (in 3.x they ran only when `_listen_update` raised `SkipHandler`
  for an unknown type, which no longer happens) (proposed default: keep the 3.x mechanics, so such handlers
  effectively never run; add no new "run after `UNHANDLED`" behaviour; registering a user `dp.update` handler emits an
  `AiogramDeprecationWarning` pointing to `unknown_update` / outer middlewares, with a migration-registry entry) —
  record in Notes and flag to owner.
- [ ] Migration-registry entries (PD-13): breaking change 9 (unknown updates go to `unknown_update`), `UpdateTypeLookupError`
  no longer raised; changelog fragment.
- [ ] Tests: admission blocks at the limit and releases; `process` returns the reply; shell and unknown-type routing;
  outer middleware sees shells; strict mode; remount identity rules (D103: identity within a view).

## Acceptance criteria

- With `tasks_concurrency_limit=N`, the (N+1)-th `feed` awaits until one task completes (test with events).
- A poison element (valid id, invalid body) reaches `unknown_update` and one `errors(phase=DECODE)`, and other updates
  in the same batch are processed (with E-15).
- A handler-returned method is rendered under the context captured at return (D-10 stub lazy object), and a silent
  call that raises (Retry give-up) produces exactly one `runtime_errors` event while the update still completes.
- Re-mounting a 100-update batch to another bot costs O(1) per update (bench: ≤ 1 µs per `as_()` on the A-05 model
  micro-bench; 3.x 179 µs).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One `feed()` that both schedules and returns a reply | A scheduled update has no reply yet | R12 |
| Raise on unknown update types | Stalls bots on every Bot API addition | D10 |
| Re-validate through dict to remount | 179 µs; replaced by bound views | D103 |
| New `TelegramDecodeError` class | Keep `ClientDecodeError` with `.raw` | PD-29 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- If B-13 is a no-go, only the remount line is re-planned (the redesigned model layer must still offer an O(1)
  rebinding or the 3.x round trip returns).
- E-15/E-16/E-17 call `feed`/`process`; H-14 `WorldSource` calls `feed`.
- Inputs: D-09 `decode_update` (bytes on every feed path), D-10's captured-call type (produced at E-02's seam by
  G-06), E-12 `emit_runtime_error`.

## Notes
