# G-10 — Utils removals and rewrites

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [A-11](../A-contracts/A-11-migration-registry.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md), [G-03](G-03-i18n-core.md) |
| Blocks | [G-11](G-11-generated-utils-signatures.md), [I-16](../I-distribution/I-16-codemod-imports-removals.md), [I-20](../I-distribution/I-20-examples-port-smoke.md) |
| Gate-conditional | no |
| Decisions | D13, D14, D15, D62, PD-13 |
| Sources | [11-removals.md §4, §7, §8](../../research/11-removals.md), [16-support-policy.md §1–§2](../../research/16-support-policy.md), [06-utils.md §2, §4](../../research/06-utils.md), [plans README §1 PD-13](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

11 §4 lists the compat-only and pydantic-only code in `aiogram/utils` that 4.0 removes or replaces. Each removal
needs a migration-registry entry (PD-13), so that the 3.x baseline warnings (3x-21..3x-23), the checker (I-14..I-19)
and the migration guide (J-02) agree.

## Scope

**In** (paths on `dev-3.x`, carried to `dev-4.x`):
- **Remove `aiogram/utils/markdown.py`** (D13), `tests/test_utils/test_markdown.py`, and any docs references to it. There is no dedicated page in `docs/utils/`;
  grep `docs/` for `utils.markdown`.
  Rewrite the three examples that use it, `examples/echo_bot_webhook.py`, `examples/echo_bot_webhook_ssl.py` and
  `examples/specify_updates.py` (`hbold`, `hcode`), to `aiogram.utils.formatting` or `html.bold(html.quote(x))`.
- **Remove `aiogram/utils/mixins.py`** (`ContextInstanceMixin`, `DataMixin`) and `tests/test_utils/test_mixins.py`.
  The only user is 3.x `aiogram/utils/i18n/core.py`, which G-05 rewrites; this plan depends on G-03, and must land
  after or with G-05 (see Workflow notes).
- **Remove the `deep_linking` re-exports** of `create_telegram_link`, `encode_payload` and `decode_payload` from
  `aiogram/utils/deep_linking.py` `__all__`. Their homes are `aiogram.utils.link` and `aiogram.utils.payload`.
- **Remove the deprecated `parameter=` argument** of `create_channel_bot_link` (`aiogram/utils/link.py`) and its
  tests in `tests/test_utils/test_link.py`.
- **Replace `WebAppUser` / `WebAppChat` / `WebAppInitData`** (hand-written pydantic `TelegramObject`s in
  `aiogram/utils/web_app.py`) with frozen dataclasses. `parse_webapp_init_data` / `safe_parse_webapp_init_data` keep
  their signatures. Keep the 06 §5 security rules: `hmac.compare_digest`, `parse_qsl(strict_parsing=True)`
  semantics, last duplicate wins.
- Migration-registry entries (PD-13) for each item above, kind `removal-4.0`, each with its replacement.

**Out:**
- `ChatMemberAdapter` (`aiogram/utils/chat_member.py`) → replaced by the generated union decoder, keep-or-remove
  decided and registered by C-19.
- `serialization.py` (`deserialize_telegram_object`) re-based on the encoder: D-14 (3x-13 fixes the SSL cost in 3.x).
- `MediaGroupBuilder` `UNSET_PARSE_MODE` → `Default("parse_mode")`: G-11.
- `force_reply` on `InlineKeyboardBuilder.as_markup` / `ReplyKeyboardBuilder.as_markup` is **kept**: Bot API 10.4
  added `force_reply` to both markups (#1954), so it is a real field, not a leak. 11 §4 / §7 are stale (A-02 fixes
  the research); no removal, test deletion or registry entry here.
- Codemod rewrites for these removals: I-16. 3.x warnings: 3x-21..3x-23.

## Checklist

- [ ] Remove `utils/markdown.py`, its tests and docs; rewrite the 3 examples (9 uses).
- [ ] Remove `utils/mixins.py` and its tests (coordinate with G-05; never leave `aiogram.utils.i18n` importing it).
- [ ] Trim `deep_linking.__all__` and imports; update `tests/test_utils/test_deep_linking.py`.
- [ ] Drop `create_channel_bot_link(parameter=)`; update tests.
- [ ] WebApp frozen dataclasses with the same field names. Port `tests/test_utils/test_web_app.py` unchanged where
      possible.
- [ ] **Decide whether the WebApp dataclasses keep `model_*` aliases** (proposed default: no; they were never Bot API
      types and the D91 alias subset covers only generated types; the checker flags `.model_dump()` on them).
      Record in Notes and flag to owner.
- [ ] One registry entry per removal (`aiogram/_migration/registry.toml`, A-11 schema, ids allocated per A-11).
- [ ] Changelog fragments (`removal`).
- [ ] Tests (100% coverage of new code).

## Acceptance criteria

- `import aiogram.utils.markdown` and `import aiogram.utils.mixins` raise `ModuleNotFoundError`.
- `from aiogram.utils.deep_linking import encode_payload` raises `ImportError`, while
  `from aiogram.utils.payload import encode_payload` works.
- `parse_webapp_init_data` returns a frozen dataclass; the ported signature tests pass.
- Every removed item has a registry entry. The registry CI check (I-12) passes.
- All three rewritten examples pass the examples smoke run (I-20, or a local import + MockedBot run).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping `utils.markdown` as a deprecated shim | Removal is decided; formatting nodes are primary | D13, D62 |
| WebApp types as butcher-generated types | Not Bot API types | 11 §4 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Needs the registry schema (A-11) and the 4.x registry CI (I-12).
- Land together with or after G-05 (mixins removal). If G-05 is not ready, split the mixins removal into a follow-up
  commit inside G-05 and note it here.
- Outputs: I-16 (codemod import rewrites), I-20 (examples), J-02 (migration guide lines from the registry).

## Notes
