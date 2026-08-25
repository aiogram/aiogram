## MODIFIED Requirements

### Requirement: Only start links are followed, and the rest are refused by name

The toolkit SHALL classify every `t.me` / `telegram.me` / `tg://resolve` url, and every other
`tg://<host>` url, into the kind Telegram documents at https://core.telegram.org/api/links —
one policy per kind, not one bucket for "recognized" and another for "everything else". `start`
SHALL be the only followable kind, including a link with no query, which SHALL parse as a plain
start with no payload. A `start` payload SHALL be honored alongside any other query parameter,
since a real client reads the parameter it recognizes and ignores the rest; that precedence
SHALL hold in either query order, so a link carrying both `start` and a Mini App, group or
channel launch SHALL be followed as the start it also is. The precedence SHALL need a real
`start` to take it, so one of those kinds appearing alone is refused as before.

Every other documented kind SHALL be refused with a message naming that kind and what a real
client does with it, rather than being replayed as a plain start or lumped into a generic
rejection: group, Mini App, channel and attachment-menu launches; a direct Mini App link and a
game-share link; an affiliate-referral link; a profile link; a prefilled-draft link; chat invite
links (including the legacy `joinchat` path and the `tg://join` form); a phone-number link,
told apart from an invite link by its all-digit tail rather than folded into the same kind; a
message link and its threaded and private-channel forms; a story link; a share link; an invoice
link, on its `$<slug>`, `/invoice/<slug>` and `tg://invoice` forms alike; a boost link, on its
path, query and `tg://` forms; a video-chat link, including its `livestream` and legacy
`voicechat` query spellings; a business-chat link; a sticker- or emoji-set link; and any Telegram
service link (a proxy, theme, language pack, wallpaper, login code, chat folder or an app
screen). Where the toolkit models the action a link only opens a screen for, the message SHALL
point at the trigger that does: an invoice link SHALL point at `pay()` and `pre_checkout_query()`,
a boost link SHALL point at `boost()`, and a prefilled-draft link SHALL name the text it would
have left unsent and point at `send()` with that text. A `tg://` url whose host is not `resolve`
SHALL still be classified as a Telegram link — by host where the host is one of the documented
ones, and as a service link otherwise — never reported as "not a Telegram link" merely because
its host is unfamiliar. A url that addresses neither a bot nor any other documented Telegram
surface SHALL be refused as not a Telegram link at all.

A `start` payload SHALL be validated against the alphabet Bot API deep linking defines —
`A-Z`, `a-z`, `0-9`, `_` and `-`, 1 to 64 characters — before being followed. A payload outside
that alphabet SHALL be refused naming the rule, rather than delivered to the handler, since a
real client never sends `/start` for a link its own payload makes invalid.

#### Scenario: A bare profile link replays as a plain start

- **WHEN** the button's url is `https://t.me/<bot>` with no query
- **THEN** following it sends `/start` with no payload

#### Scenario: An explicit start wins over a start-ish parameter beside it

- **WHEN** the button's url carries both `start` and one of `startapp`, `startgroup` or
  `startchannel`, in either order
- **THEN** following it sends `/start` with the `start` payload rather than being refused

#### Scenario: Every documented format is refused as the format it is

- **WHEN** the button's url is one of the link forms https://core.telegram.org/api/links
  documents — a direct Mini App link, a message link, a story link, a share link, an invoice
  link, a boost link, a video-chat link, a business-chat link, a sticker-set link, a
  prefilled-draft link, an affiliate-referral link, a profile link, or a service link such as a
  proxy or language pack
- **THEN** following it raises, naming that kind and what a real client does with it, and — for
  an invoice or a boost link — pointing at the trigger (`pay()`, `pre_checkout_query()`,
  `boost()`) that models the underlying action instead

#### Scenario: A phone link is not mistaken for an invite link

- **WHEN** the button's url is `t.me/+<digits>` or `tg://resolve?phone=<digits>`
- **THEN** following it raises naming it a phone-number link, and the message does not call it
  an invite link

#### Scenario: A `tg://` host other than `resolve` is still a Telegram link

- **WHEN** the button's url is a `tg://` url whose host is not `resolve`, whether or not the
  toolkit enumerates that host by name
- **THEN** following it raises naming the kind that host documents, or naming it a Telegram
  service link when the host is not individually enumerated — never claiming the url is not a
  Telegram link

#### Scenario: An unsupported kind is named, not downgraded

- **WHEN** the button opens a group chooser, a Mini App, a channel chooser or the attachment
  menu, with no `start` beside it
- **THEN** following it raises, naming that kind and what to do instead, rather than sending
  a plain `/start`

#### Scenario: A start payload outside the deep-linking alphabet is refused

- **WHEN** the button's `start` payload is longer than 64 characters, percent-encoded, or
  otherwise outside `A-Z`, `a-z`, `0-9`, `_` and `-`
- **THEN** following it raises naming the deep-linking payload rule, and no `/start` is sent to
  the handler

#### Scenario: An unrecognized query is refused rather than guessed

- **WHEN** the button's url carries a query parameter none of the documented kinds define
- **THEN** following it raises, saying that what a real client would do with it is not
  simulated

#### Scenario: The scan skips what it cannot follow

- **WHEN** a keyboard carries both an unfollowable deep link and a real start link to this bot
- **THEN** the start link is followed; and when only unfollowable ones are present, the
  failure names each url and why it was rejected
