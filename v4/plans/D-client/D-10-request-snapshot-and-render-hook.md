# D-10 — Request snapshot and lazy-text render hook (context captured at return and at call)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [D-04](D-04-drop-aiofiles-input-file-replayable.md), [D-06](D-06-request-middleware-manager.md), [D-07](D-07-rust-encoder-json.md), [D-08](D-08-rust-encoder-multipart.md), [B-09](../B-spike/B-09-sendmessage-encoder-response.md) |
| Blocks | [D-11](D-11-session-on-new-codec.md), [D-14](D-14-webhook-reply-encoding.md), [G-06](../G-features/G-06-lazy-text-capture.md), [G-13](../G-features/G-13-retry-middleware.md), [G-09](../G-features/G-09-lazy-text-trees.md), [H-12](../H-testing-observability/H-12-toolkit-model-api-migration.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [E-16](../E-runtime/E-16-webhook-core-aiohttp-sources.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | D117 (narrowed by PD-07), R19, R21, D61 |
| Sources | [05-network.md §2.1](../../research/05-network.md), [06-utils.md §3, D61](../../research/06-utils.md), [19 §1 D117, §2 R19](../../research/19-review-resolutions.md), [codex-review.md R19, R21](../../research/codex-review.md), [plans README §1 PD-07](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Two G features need a request **snapshot**:
- Lazy text (D25/D61, G-06): display fields hold lazy objects; the encoder renders text **and** entities once, with the
  i18n context captured. PD-07 narrows D117: the context is captured **when a handler returns a method and when
  `bot(method)` is called**; constructors stay i18n-free.
- `RetryMiddleware` (G-13, R19): retries reuse the same rendered request, and an upload whose non-replayable
  `InputFile` was already consumed is never silently resent.

Request middlewares see `(bot, method)` and encoding happens innermost in `make_request`, so nothing today carries a
snapshot between attempts. This plan defines the carrier and the encoder's render callback. It owns the mechanism,
not the i18n engine.

## Scope

**In:**
- Snapshot fields on D-06's per-call request context (D-06 owns the object, `timeout` and `attempt`; this plan
  adds to it rather than creating a second carrier): holds `bot`, the method, the captured render context, the lazily built encoded body (`JsonBody | Multipart`), and
  per-file "consumed" flags.
- Capture points (PD-07): `Bot.__call__` / `BaseSession.__call__` capture the current render context; for a handler
  return value this plan provides a small public function (e.g.
  `aiogram.client.session.capture_context(method) -> CapturedCall`) that G-06 installs at E-02's handler-result seam.
  E-14, E-16 and D-14 only receive the resulting `CapturedCall` (silent call, webhook reply); they never call
  `capture_context` themselves.
- Encoder render hook: `encode(method, defaults, render=callable | None)`; for each value implementing the
  lazy-text protocol (`__aiogram_render__(ctx: RenderContext) -> tuple[str, tuple[MessageEntity, ...] | None]` — the protocol is owned by G-03; this plan owns the encoder render hook and its call
  contract), the encoder calls `render` once and uses the returned text and entities together.
  Explicit `entities`/`parse_mode` next to a lazy `Text` raise `ValueError` (D61).
- **Python-callable resolve/render step** (consumed by H-12's fake session): a public function (proposed
  `aiogram.client.session.resolve_method(method_or_captured_call, bot) -> TelegramMethod`) that returns a **resolved
  method object, not bytes** — `Default(...)` values resolved against `bot.default`, lazy display values rendered once
  under the captured context into text + entities. It shares the render callback and default resolution with the
  encoder, so the fake and the wire see the same values (no second resolver).
- Reuse rules: the snapshot is built on first `make_request` and reused by later attempts of the same call if the
  method object is identical; a middleware that passes a different (replaced) method causes a re-encode.
- Replayability: after a multipart send, files with `replayable is False` are marked consumed; re-sending a snapshot
  with a consumed file raises a clear error (G-13 checks first and skips the retry).

**Out:**
- Lazy-text objects, engines, locale context → G-03/G-06. Retry policy → G-13.
- Session wiring → D-11. Webhook reply encoding → D-14 (uses this capture).

## Checklist

- [ ] Snapshot fields on the per-call carrier decided in D-06's Decide item (not re-decided here); the identity check
      on the method decides reuse vs re-encode.
- [ ] Capture at `bot(method)` and the public capture function for handler returns (PD-07).
- [ ] Encoder `render` callback, text + entities from one call; `ValueError` on explicit entities/parse_mode.
- [ ] Consumed-file tracking for non-replayable `InputFile`s.
- [ ] Python-callable resolve/render step returning a resolved method (not bytes), sharing the encoder's render and
      default resolution (H-12 calls it).
- [ ] Tests with a stub lazy object (no i18n engine): rendered once across two attempts; replaced method re-renders;
      two concurrent calls under two contexts render independently (non-BMP text, nested entities — R21 acceptance).
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`misc`; user-facing docs come with G-06).

## Acceptance criteria

- A request middleware calling `next` twice triggers exactly one render and one encode (counting stubs).
- Encoding one keyboard containing lazy button texts concurrently under two captured contexts yields two independent
  bodies with correct UTF-16 entity offsets for a non-BMP string.
- A second attempt with a consumed non-replayable file raises (message names the file field) instead of sending an
  empty part.
- The resolve/render step on a method with `parse_mode=Default("parse_mode")` and a lazy `text` returns a method
  object (not bytes) whose `parse_mode` equals `bot.default.parse_mode` and whose `text`/`entities` equal what the
  encoder puts on the wire for the same captured context.
- No measurable overhead when no lazy values are present: pinned `SendMessage` encode within 5% of D-07's number.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Capture the context in method constructors | Constructors stay i18n-free | PD-07 |
| Re-render per attempt | Text/entity mismatch across retries | R19, R21 |
| Encode before the middleware chain | Middlewares could no longer replace the method before encoding | 05 §2.3 (middleware API kept) |
| Store the snapshot on the method | Methods are frozen (D15) and may be shared across calls | D15 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-06 (chain and the per-call carrier, decided there), D-07/D-08 (encoder), D-04 (`replayable`).
- Outputs: `capture_context` installed by G-06 at E-02's handler-result seam, and the `CapturedCall` type that
  E-14, E-16 and D-14 receive (they never capture), render hook (G-06), snapshot reuse and consumed
  flags (G-13), attempt/call info that H-07 reads, the Python-callable resolve/render step (H-12).

## Notes
