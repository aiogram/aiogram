## 1. Parsing

- [x] 1.1 Add `_parse_deep_link` recognizing `https://t.me/<username>`, its `http://` and
      schemeless forms, and `tg://resolve?domain=<username>`
- [x] 1.2 Classify the query parameter kinds — `start`, `startgroup`, `startapp`,
      `startchannel`, `startattach`, `attach` — by iterating the policy table (design D2)
- [x] 1.3 Classify the path-derived kinds: `+hash` and `joinchat/hash` invite links, and any url
      with extra path segments (design D6)
- [x] 1.4 Parse a link with no query as `start` with an empty payload (design D4)
- [x] 1.5 Let `start` win alongside any other query parameter, and bucket a query carrying none
      of the known keys as `unknown_query` (design D3)
- [x] 1.6 Return `None` only for urls that are not Telegram links at all

## 2. The policy table

- [x] 2.1 Add `_LINK_KINDS`, one row per kind, carrying whether it is followable and the
      rejection message (design D2)
- [x] 2.2 Derive `_QUERY_PARAM_KINDS` as the complement of `_PATH_DERIVED_KINDS` in the table,
      so the two cannot drift
- [x] 2.3 Write each rejection to name the kind, what a real client would do with it, and what
      to do instead — `startgroup` points at `add_bot()`

## 3. Following

- [x] 3.1 Add `UserActor.follow_deep_link(target=None, *, message=None, **data)` accepting a url
      string, an `InlineKeyboardButton`, or nothing
- [x] 3.2 Require the url to be carried by a button of a message in scope, exactly as `click()`
      requires the callback data (design D1)
- [x] 3.3 Reject path-derived kinds before comparing the username (design D6)
- [x] 3.4 Reject a link to another bot, and any kind that is not followable
- [x] 3.5 Replay as `/start <payload>` — or a bare `/start` — through a fresh unbound actor for
      the same user (design D1)
- [x] 3.6 Tests: the happy path with and without a payload; the `tg://resolve` form; harmless
      extra query parameters; a button carrying no url; a url that is not on the message; each
      unfollowable kind refused by name

## 4. The automatic scan

- [x] 4.1 Walk buttons newest-first through the shared `_iter_buttons`, which `click()` also
      uses, and take the first followable link to this bot (design D5)
- [x] 4.2 Remember unfollowable links to this bot as candidates instead of ending the scan
- [x] 4.3 Skip buttons with no url and buttons linking to another bot
- [x] 4.4 Name every candidate and its reason when nothing followable was found, distinguishing
      an explicit `message=` from a whole-chat scan
- [x] 4.5 Tests: the newest matching button wins; the scan looks past a Mini App button to the
      `start` link; a scan with only unfollowable candidates names each and why; buttons to
      another bot are skipped; `message=` scopes the search

## 5. The private chat that opens on demand

- [x] 5.1 Add `private_chat_shape(user)` and use it from both `Blueprint.add_private_chat` and
      the world, so a chat opened on demand is shaped exactly like a declared one (design D7)
- [x] 5.2 Add `World.ensure_private_chat(user)`, registering the chat so its messages are bound
      like any declared chat's
- [x] 5.3 Route `UserActor.chat` for an unbound actor, and `in_()` on the actor's own id,
      through it
- [x] 5.4 Keep every other undeclared chat raising
- [x] 5.5 Tests: a followed link opens an undeclared private chat; a plain `send()` from an
      unbound actor opens it too; an actor without a declared private chat gets one

## 6. Documentation

- [x] 6.1 Add a "Deep links" section to `docs/dispatcher/testing.rst` with the "Continue in DM"
      recipe
- [x] 6.2 List the recognized url forms, state that a bare profile link is followable, and name
      the kinds that are refused
- [x] 6.3 State the private-chat rule where the blueprint is introduced: a user's own DM opens on
      demand, every other chat must be declared
- [x] 6.4 Build docs and fix any new warnings

## 7. Release readiness

- [x] 7.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry
- [x] 7.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview
      aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q
      --cov=aiogram --cov-report=term-missing` at 100%
