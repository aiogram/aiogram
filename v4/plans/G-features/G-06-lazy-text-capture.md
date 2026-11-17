# G-06 — Lazy text in display fields, with i18n context capture (D117 / PD-07)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-03](G-03-i18n-core.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-14](../D-client/D-14-webhook-reply-encoding.md), [C-06](../C-butcher/C-06-overlay-schema-loader.md), [C-14](../C-butcher/C-14-pyi-stub-emitter.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md), [E-02](../E-runtime/E-02-dispatch-table-executor.md) |
| Blocks | [G-09](G-09-lazy-text-trees.md), [G-20](G-20-aiogram-i18n-final-release.md), [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md) |
| Gate-conditional | **yes** (lazy values are stored in Rust-native frozen types, D4/D104; re-validate after B-13) |
| Decisions | D25, D117, PD-07, D15, D108, D106, PD-08 |
| Sources | [06-utils.md §3](../../research/06-utils.md), [01-models.md §3.5](../../research/01-models.md), [05-network.md §2.1, §2.3](../../research/05-network.md), [19 D117, R18, R19](../../research/19-review-resolutions.md), [codex-review.md R21](../../research/codex-review.md), [plans README §1 PD-07](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The goal is for one keyboard literal to serve every locale: `InlineKeyboardButton(text=L.buy(), …)` defined at
import time is rendered with the user's locale when the request is built.

3.x has a bug here (19 "new issues"): returned methods are encoded **after** the i18n middleware's context exits. A
webhook inline reply or a polling silent call (`Dispatcher.silent_call_request`, 3.x
`aiogram/dispatcher/dispatcher.py`) therefore renders in the wrong locale.

D117, as narrowed by **PD-07**: the i18n context is captured **when a handler returns a method** and **when
`bot(method)` is called**. Method constructors stay i18n-free, so there is no `ContextVar` read on the Rust
construction hot path.

## Scope

**In:**
- **Display-text fields accept lazy values.** C-06 marks them in the overlay (`text`, `caption`, `title`,
  `description`, button `text`, …). The generated Rust types store the lazy object unchanged (frozen-safe, D15), and
  C-14 emits their stub type as `str | LazyText` (`LazyText` from `aiogram/_lazy.py`, C-14; implemented by G-03). This plan integrates lazy values into frozen-type storage and the
  capture: the runtime class check the Rust side calls (protocol owned by G-03) and the tests. D-10 owns the encoder
  render hook.
- **Capture points (PD-07)**:
  1. When a handler returns a `TelegramMethod`: this plan installs D-10's capture at E-02's handler-result seam, so
     the render context is captured right at return, still inside the middleware scope (where the i18n middleware's
     context is live). The E-14 / E-16 feed paths (polling silent call, webhook inline reply via D-14) only carry the
     captured call; they never capture after the outer chain has unwound.
  2. `bot(method)` / `await method` captures the current render context when called.

  No other capture point exists. A method built in one task and sent from another renders with the context of the
  sending call.
- **Encode-time render** through D-10's request snapshot + render hook. Each lazy field is rendered once per request
  snapshot, and retries reuse it (R19). The encoder must not hold Rust locks while it calls the Python render (06 §3
  risk). This plan supplies the Python render callable D-10 invokes and the context object it carries.
- **Fallback paths**: under PD-08 the Bot API wire always uses the Rust codec, whatever the session `json_*` hooks
  say. If D-12 keeps a Python `prepare_value` path for sessions that override it (05 §2.3), that path must render
  lazy values with the same captured context and snapshot. Add a test to D-12's hook-compatibility suite, or record
  in Notes that D-12 removed the path.
- **Outside any update and without `use_locale`**: render with the engine default locale. With no i18n configured at
  all, raise `I18nNotConfiguredError` at encode, naming the field.
- Docs: lazy text in keyboards and captions, capture rules (return / call), and the background-task caveat.

**Out:**
- Lazy values inside `Text` formatting trees, with entities: G-09.
- The render hook inside the encoder and the request snapshot object: D-10.
- The display-field overlay marks: C-06. Stub emission: C-14.

## Checklist

- [ ] Capture installed at E-02's handler-result seam (return) and at `bot(method)`; E-14 / E-16 carry the captured
      call to the silent call and the webhook reply.
- [ ] Render callable + error mapping for D-10. Rendered values are cached in the request snapshot.
- [ ] Verify that `deserialize_telegram_object` (3.x `aiogram/utils/serialization.py`; D-14 re-bases it on the
      encoder) renders lazy values with the captured context.
- [ ] **Decide lazy-value semantics inside frozen types** (R21; 19 is silent). Proposed defaults:
  - `==` compares the lazy object (key + kwargs), not a rendering;
  - `hash` is that of the lazy object (immutable key + frozen kwargs), so D108 hashability holds;
  - pickle keeps the lazy object;
  - `.raw` / `to_dict()` / `to_json()` / `TelegramMethod.to_json()` (model representation, R18) render with the
    **current** context if one is active and otherwise raise `I18nNotConfiguredError` (no silent key leak);
  - `.raw_json` of a constructed object follows `to_json()` (D108).

  Record in Notes and flag to owner.
- [ ] **Decide whether wire-decoded objects ever contain lazy values** (proposed default: never; only user-constructed
      objects can) — record in Notes.
- [ ] Concurrency test (R21): one keyboard literal encoded concurrently under `en` and `uk`, including non-BMP text.
      Outputs are independent, and a retried request reuses the first rendering.
- [ ] Docs page and examples.
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`feature` + `bugfix` for the 3.x "encoded after context exits" behaviour).
      Migration-registry entry (PD-13) describing the changed render moment for 3.x code that called `str(__("x"))`
      eagerly (kind `removal-4.0`, informational).

## Acceptance criteria

- Webhook inline reply and polling silent call: a handler under locale `uk` returning
  `SendMessage(text=L.hello(), reply_markup=kb_with_lazy_buttons)` produces a request body in `uk` (MockedBot +
  webhook test client).
- The concurrency test above passes 1 000 iterations without cross-locale leakage.
- A retried request (D-10 snapshot reused) has a byte-identical body on every attempt, even when the locale is
  switched between attempts.
- Constructing a method with a lazy field performs **no** `ContextVar` read. Asserted by patching the `ContextVar`
  and constructing 10 000 methods.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Capture in method constructors ("created inside an update") | `ContextVar` read on the Rust construction hot path; couples types to i18n | PD-07 (narrows D117) |
| Render lazily on every attribute read | Text and entities could mismatch; retries could render differently | D117, R21 |
| Letting session `json_dumps` hooks see unrendered lazy values | Wire always uses the Rust codec, and lazy values are rendered before any hook | PD-08 |
| `aiogram_i18n`-style pydantic `LazyProxy` | aiogram types are no longer pydantic | D25, D14 |

## Validation

```bash
cargo fmt --check && cargo clippy -- -D warnings && cargo test
make dev
cargo xtask butcher check
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Gate-conditional: start only after B-13 records *go*.
- Inputs:
  - C-06 display marks;
  - C-14 stubs;
  - D-10 request snapshot + render hook;
  - D-14 webhook reply encoding;
  - E-02 handler-result seam (return capture); E-14 feed paths (carry the captured call);
  - G-03 render protocol.
- Outputs: G-09 builds lazy `Text` on the same capture and snapshot. G-13 relies on "rendered once per snapshot".
  I-19 may add a heuristic rule for eager `str(__())` at import time.

## Notes

- Coordinator default (reconciliation, K1): return-time capture is installed at E-02's handler-result seam, inside the
  middleware scope; E-14 / E-16 do not capture.
