# Tasks

## 1. `match_by` slot generalization

- [x] 1.1 Replace `_LinkKindPolicy.addresses_username: bool` with `match_by: str`
      (`_MATCH_USERNAME` / `_MATCH_PAYLOAD` / `""`), and set `attach`'s row to
      `match_by=_MATCH_PAYLOAD` (design D1)
- [x] 1.2 Add `_addressed_bot(deep_link)` and route `follow_deep_link` and
      `_find_deep_link_url` through it instead of their own `deep_link.username` comparisons
      (design D2)
- [x] 1.3 `_path_deep_link`'s phone branch and the `tg://resolve` phone branch defer to the
      query and read no username when `attach` is present alongside a phone number

## 2. Empty `start` no longer wins

- [x] 2.1 Narrow the pre-table `start` check in `_parse_deep_link` to `starts and starts[0]`
      (design D3)
- [x] 2.2 Regression tests: `?start=&startapp=y` (and reordered, and `tg:` forms) classify as
      `startapp`; a bare `?start=` alone is unchanged

## 3. Companion-parameter precedence

- [x] 3.1 Add `_COMPANION_QUERY_KEYS` and build `_QUERY_KIND_LOOKUP` with
      `sorted(..., key=lambda pair: pair[0] in _COMPANION_QUERY_KEYS)` in place of the static
      aliases-first order (design D4)
- [x] 3.2 Regression tests: `?startapp=x&text=y`, `?startattach&text=y`, `?text=hi&profile`,
      `?startgroup=g&text=hi`, and `?appname=shop&startapp=ref` all classify by the owning
      format; each companion alone still names its own kind

## 4. `channel_preview` kind

- [x] 4.1 Reserve `"s"` to `"channel_preview"` in `_RESERVED_PATH_KINDS`, checked ahead of the
      direct-Mini-App path shape (design D5)
- [x] 4.2 Tests: `t.me/s/<username>`, `.../<post>` and bare `t.me/s` refused as a web-preview
      link, `"Mini App"` absent from the message; the scan ignores such a button; the
      `/<username>/s/<n>` story shape is unaffected

## 5. `validate_payload` escape hatch

- [x] 5.1 `follow_deep_link(..., validate_payload: bool = True)`, gating the existing
      `_require_valid_start_payload` call (design D6)
- [x] 5.2 Tests: an out-of-alphabet payload replayed as-is through both the explicit-target and
      scan forms; the default still refuses the same payload; a non-`start` kind is still
      refused with the flag set

## 6. Documentation

- [x] 6.1 `docs/dispatcher/testing.rst` Deep links subsection: `attach`'s own sentence,
      non-empty-`start` wording plus the `?start=&startapp=y` line, the companion-precedence
      sentence, the `channel_preview` mention, and the `validate_payload=False` paragraph

## 7. Spec sync

- [x] 7.1 `bot-testing-environment`: amend "Deep-link buttons can be followed" with the
      per-kind bot-matching-slot paragraph and its scenario; amend "Only start links are
      followed, and the rest are refused by name" with the non-empty-`start` rule, the
      companion-precedence rule and scenario, the `channel_preview` kind and scenario, and the
      `validate_payload` rule and scenario

## 8. Release readiness

- [x] 8.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry
- [x] 8.2 Full check loop green: `ruff format`, `ruff check --show-fixes --preview aiogram
      examples`, `mypy aiogram`, `pytest tests -q`
