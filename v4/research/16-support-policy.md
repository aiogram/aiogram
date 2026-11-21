# 16 — Deprecation policy and 3.x support

| # | Decision |
|---|---|
| **D71** | **One deprecation window for everything.** aiogram's own APIs use the same shape of rule as the Bot API ledger (D6), counting aiogram minor releases where the ledger counts Bot API majors. A feature is deprecated in a 4.x minor, with a warning that names the replacement and the earliest removal version. It is removed no earlier than **the later of 12 months and 2 minor releases** after that. Removals may land in minors; each is listed under `CHANGES/*.removal.rst`. The 4.0 ledger reset (02 §4) is an **explicit exception** to this rule (R28) |
| **D72** | **`AiogramDeprecationWarning(DeprecationWarning)`**, with aiogram installing a `default` filter for this category at import **only `if not sys.warnoptions`** (R28), so each deprecation is shown once per call site even outside `__main__`. Users silence or escalate it by category through pytest config (`filterwarnings = ["error::aiogram.AiogramDeprecationWarning"]`) or `warnings.filterwarnings("error", category=AiogramDeprecationWarning)` in code; `-W error::aiogram.AiogramDeprecationWarning` doesn't work, because CPython rejects the module path ("invalid module name"). Bot API ledger warnings use the subclass `AiogramApiDeprecationWarning` |
| **D73** | **3.x support after 4.0.0 GA**: **12 months full support** (Bot API bumps via legacy butcher, bugfixes, 09 quick wins), then **6 months security-only**, then EOL. The exact dates are published in the 4.0.0 release notes and docs. butcher stays maintained for the 3.x branch until the full-support phase ends |
| **D74** | **Bridges for 3.x users**: (1) deprecations in a named **migration-baseline 3.x release** (R28), kept in every later 3.x release, (2) a codemod, (3) a migration checker (§2) |

## 1. Rules for a deprecation

- Each deprecation is listed in the docs ("Deprecations" page, generated from the migration registry), with the
  version in which it was deprecated, the earliest removal version and the replacement. The registry is one data file,
  `aiogram/_migration/registry.toml`, read by path (PD-13, 18 §2). After the fork `dev-4.x` owns it, with id blocks
  per branch (PD-33, A-11).
- Warnings fire at the earliest point that has no runtime cost:
  - at **registration**, when a handler, filter or middleware signature or argument uses something deprecated
    (`CallableObject` already inspects signatures);
  - at **import**, for deprecated modules;
  - on **first use**, for attributes and methods.
- Tests: one test per deprecation asserting that the warning is raised and that the replacement works. The removal
  PR deletes both. An entry becomes **due** under the D71 rule (R28): 12 months **and** 2 minors after its
  deprecation. From then on CI requires an explicit `removal_decision` on the entry (I-12); it doesn't fail merely
  because a version number was reached.

## 2. 3.x → 4.0 bridges (D74)

1. **Migration-baseline 3.x release** (named in advance, R28; its warnings stay in every later 3.x release, since
   Bot API bumps continue after GA): emits `AiogramDeprecationWarning` (backported class) for everything 4.0 removes or changes,
   each pointing to the 4.0 replacement. The list comes from 11-removals and the README breaking changes:
   - `Message.content_type` / `ContentType`;
   - `event_from_user` / `event_chat` / `event_thread_id`, warned at handler registration when they are requested as
     parameters;
   - `aiogram.utils.markdown`, `aiogram.handlers`, `MongoStorage`, `UNSET_*`, `BaseFilter`, `CancelHandler`,
     `dp[...] = ...`, `utils.mixins`, the `deep_linking` re-exports, the flat `link_preview_*` fields, `RestartingTelegram`;
   - `UnsupportedKeywordArgument`, the `Recommendation` warning, `create_channel_bot_link(parameter=)`;
   - user `TelegramMethod` subclasses (D96);
   - the API-ledger reset: the 122 deprecated Bot API fields and the 3 entities (`KeyboardButtonRequestUser`,
     `UserShared`, `StoryAreaPosition`, 11 §1);
   - pydantic-specific `CallbackData` features (`Field`, validators);
   - mutation of mutable types.

   `force_reply` on the keyboard builders is **not** on the list: it is a real Bot API 10.4 field (#1954) and stays
   (PD-32). D100 positional calls get **no runtime warning** in 3.x; only the checker reports them.
2. **Codemod**, `python -m aiogram.migrate fix <paths>`, built on libcst through the `aiogram[migrate]` extra. It
   rewrites the mechanical cases:
   - imports and renamed modules;
   - `F.content_type == ContentType.X` → `F.x`;
   - `event_from_user` → `event_context.user`;
   - `utils.markdown` calls → `formatting` nodes;
   - class-based handlers → functions where the pattern is simple;
   - `MutableTelegramObject` attribute writes: `obj.x = y` → `obj = obj.replace(x=y)` **only on plain names**
     (the result is always reassigned); attribute chains, aliases and the rest are reported, not rewritten (R28);
   - positional calls to `Bot` methods and shortcuts → keyword form, using the 3.x signature order (D100/D101). `bot.*`
     calls are resolved through `Bot` annotations; shortcut calls on `Message` / `CallbackQuery` / … are resolved where the
     receiver type can be inferred (handler parameter annotations, `isinstance`), and the rest are reported;
   - `model_*` calls → native API (`to_json`, `to_dict`, `from_json`, `from_dict`, `replace`; D91). `model_fields` has no replacement (D95); the checker flags it, and user `TelegramMethod` subclasses (D96).

   Every change is a reviewable diff, and `--dry-run` is the default.
3. **Checker**, `python -m aiogram.migrate check <paths>`, reports every 4.0 incompatibility with file and line,
   including ones the codemod can't fix, such as positional API calls whose receiver type can't be inferred (D101). Each finding has a checker id shared with the migration guide (18 §2) and is classed **definite / heuristic / manual checklist**, with a confidence level and a suppression comment (R28). Examples: bare `x.as_(bot)` statements (D103) and list comparisons on collection fields (D106) (definite where the receiver is known); SkipHandler data reliance, sibling error-handler reliance (D48),
   sync filters doing I/O (D34), isolation-sensitive code (D28) (heuristic or manual). Exit code ≠ 0 for CI use.

It is also available as `aiogram migrate …` (17). Both modes ship in **4.0**. They run on
source, so they work before the dependency is upgraded: `uvx --from 'aiogram[migrate]>=4' aiogram migrate check <path>`.

## 3. External packages (19 §8)

The final releases of `aiogram_i18n` (deprecation notice, D25) and `aiogram-cli` (no `aiogram` console script,
D77 / R30) happen in **their own repositories**. Each needs a named owner and a release date aligned with 4.0.0 GA,
tracked as a milestone J item; this repository can only document them.
