# G-09 — Lazy `Text` trees (D61)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-06](G-06-lazy-text-capture.md), [G-08](G-08-formatting-on-kernel.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-17](../D-client/D-17-rust-entity-rendering-kernel.md) |
| Blocks | [G-20](G-20-aiogram-i18n-final-release.md) |
| Gate-conditional | **yes** (builds on G-06 lazy values in Rust-native types; re-validate after B-13) |
| Decisions | D61, D117, PD-07, D62 |
| Sources | [06-utils.md §4](../../research/06-utils.md), [19 D117](../../research/19-review-resolutions.md), [codex-review.md R21](../../research/codex-review.md), [05-network.md §2.1](../../research/05-network.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`Text(Bold(L.title()), " ", L.body())` should produce the right text **and** the right UTF-16 entity offsets for
each locale. Offsets depend on the rendered lengths, so text and entities must be rendered **together, once per
request snapshot**. Otherwise a locale switch or a retry could pair a `uk` text with `en` offsets (R21).

## Scope

**In:**
- A `Text` containing at least one lazy value implements the G-03 render protocol (`__aiogram_render__(ctx: RenderContext) -> tuple[str, tuple[MessageEntity, ...] | None]`) and returns
  **`(text, entities)`**; D-10's encoder render hook consumes it.
  A plain `Text` keeps rendering eagerly, as today.
- `Text.as_kwargs()` / `as_caption_kwargs()` / … on a lazy `Text` return the lazy `Text` itself in the `text` /
  `caption` slot, and **omit** the sibling `entities` / `parse_mode` keys. D-10 fills both from one render.
- **Sibling-field replacement** in the D-10 render hook: the rendered entities go into the matching `X_entities`
  field (IR triple, the same mapping G-11 uses), and `X_parse_mode` is forced to `None`.
- **Conflicts (D117)**: explicit `entities` / `parse_mode` next to a lazy `Text` **raise** `ValueError`, at
  construction when the type can check it, otherwise at encode.
- Capture follows G-06 (return / `bot()` call, PD-07). Rendered once per snapshot; retries reuse it.

**Out:**
- Plain lazy values in display fields: G-06.
- The render hook mechanics: D-10.

## Checklist

- [ ] Lazy detection on `Text` construction (walk once; cache a flag on the node).
- [ ] Render returning `(text, entities)` with UTF-16 offsets via the D-17 kernel (G-08).
- [ ] D-10 integration: `X` / `X_entities` / `X_parse_mode` triple replacement.
- [ ] **Decide how bot-level `Default("parse_mode")` interacts with a lazy `Text`** (proposed default: a lazy `Text`
      resolves `parse_mode` to `None` regardless of `DefaultBotProperties.parse_mode`; only an *explicit*
      `parse_mode=` argument raises). Record in Notes and flag to owner.
- [ ] **Decide whether a plain `L.key()` (not inside `Text`) in a field with `parse_mode="HTML"` stays legal**
      (proposed default: yes; translations containing HTML markup are a common pattern; only lazy `Text` forbids
      `parse_mode`). Record in Notes and flag to owner.
- [ ] R21 test: one formatting tree encoded concurrently under two locales, with non-BMP characters (emoji, surrogate
      pairs) and nested entities. Text and offsets match each locale; retries are identical.
- [ ] Docs: formatting page section "Localised formatting".
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- `SendMessage(chat_id=1, **Text(Bold(L.title()), " ", L.body()).as_kwargs())` encodes to a body whose `text` and
  `entities` are correct for `en` and `uk`. Offsets are checked against the D-17 kernel on the rendered string,
  including a title with a 4-byte emoji.
- `SendMessage(..., text=lazy_text, parse_mode="HTML")` raises `ValueError` naming the conflicting field.
- The concurrency test passes 1 000 iterations without cross-locale leakage.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rendering text and entities separately | Offsets could mismatch across locale switches or retries | D117, R21 |
| Silently ignoring explicit `entities` next to a lazy `Text` | Hides user bugs | D117 |
| Capture in constructors | Narrowed to return / call | PD-07 |

## Validation

```bash
cargo fmt --check && cargo clippy -- -D warnings && cargo test
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Gate-conditional: start only after B-13 records *go*.
- Inputs: G-06 (capture + lazy fields), G-08 (kernel-backed `Text`), D-10 (render hook with sibling replacement).
- Output: G-11's generated `as_*_kwargs` must follow the "omit siblings when lazy" rule. Note it in G-11's PR if
  G-11 merges first.

## Notes
