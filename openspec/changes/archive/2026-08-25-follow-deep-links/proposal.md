## Why

The group bot the toolkit was exercised against never puts a `callback_data` button in a public
chat. It posts "Tap to get your role" with a `url` button pointing at
`https://t.me/<bot>?start=game-42`, and everything private happens in the DM the tap opens. That
is the standard pattern for anything a group must not see, and the toolkit had no way to
exercise it: `click()` refuses a button with no `callback_data`, and writing the follow by hand
means composing `/start game-42` yourself and sending it into a private chat — which is to say,
asserting nothing about the button at all.

The private chat was the second wall. A blueprint that never declared one made even the
hand-written version fail, because `.in_(alice.id)` raised on a chat "not declared in the
blueprint". But every Telegram user *can* open a DM with any bot, and tapping a `/start` link is
precisely what opens it — so a blueprint that did not declare one was never saying "this user
has no private chat", only that the test had not needed to name it.

The third problem showed up in review rather than in the PoC. A first cut treated every
recognized `t.me` url as a bare `/start`, which is wrong in a way tests cannot see: a
`startgroup` button opens a group chooser, a `startapp` button opens a Mini App, and replaying
either as `/start` would make a test pass against a flow the bot never has.

## What Changes

- **`UserActor.follow_deep_link(target=None, *, message=None)`** follows a deep-link `url`
  button of a message the bot actually sent, with `click()`-grade validation: the button must
  really be there. It then replays what tapping actually causes — the user's client opens a
  private chat with the bot and sends `/start <payload>` there.
- **The link kinds are a policy, not a parse.** `start` is followable, including a bare profile
  link with no query, which replays as a plain `/start`. Every other recognized kind —
  `startgroup`, `startapp`, `startchannel`, `startattach`, `attach`, chat invite links, links
  with extra path segments such as message links and Mini App shortlinks, and any query
  Telegram does not define — is refused **by name and with a reason**, rather than quietly
  downgraded.
- **The automatic scan skips what it cannot follow.** With no target, the newest followable
  link to *this* bot wins; a keyboard mixing a Mini App button with a real `start` link still
  finds the `start` link, and one carrying only unfollowable candidates fails naming each and
  why.
- **A user's own private chat opens on demand.** `World.ensure_private_chat` builds it from the
  same description `Blueprint.add_private_chat` uses, and it is reached three ways: a followed
  deep link, a plain `send()` from an unbound actor, and `.in_(own id)`. Any *other* undeclared
  chat still raises — the world cannot invent a group's title, type or membership from a bare
  id.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: actors gain deep-link following as stated behavior, and the rule
  that a user's own private chat is not something a blueprint has to declare.

## Impact

- **Code**: `actors.py` (`follow_deep_link`, `_parse_deep_link`, the `_LINK_KINDS` policy table
  and the shared button walk `_iter_buttons` that `click()` also uses); `world.py`
  (`ensure_private_chat`, `private_chat_shape` shared with the blueprint); `UserActor.chat` and
  `UserActor.in_` route the actor's own id through it.
- **Tests**: a new `tests/test_testing/test_deep_links.py`.
- **Docs**: a "Deep links" section in `docs/dispatcher/testing.rst`, plus the private-chat rule
  stated where the blueprint is introduced.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry.
- **Risk**: the link policy encodes a reading of what real clients do. Where the toolkit is
  unsure, it refuses rather than guesses — an unrecognized query is its own rejected kind, not a
  silent `/start`.
