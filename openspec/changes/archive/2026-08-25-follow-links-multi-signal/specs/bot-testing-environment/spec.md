## MODIFIED Requirements

### Requirement: Deep-link buttons can be followed

A user actor SHALL be able to follow a `url` button that deep-links to the bot under test,
with the same validation a callback button gets: the button SHALL have to be carried by a
message the environment actually holds, either a named one or any message of the actor's
chat. Following SHALL replay what tapping causes in a real client — the user's private chat
with the bot receives `/start <payload>`, or a bare `/start` when the link carries none — so
filters, the command parser, middlewares and FSM all run as they do in production.

Which parsed slot of a link names "the bot" depends on the link's kind, not on a fixed
position: for every kind that addresses a bot by username, the button matches this bot when
that username is the bot's own. The attachment-menu link is the one documented exception —
`t.me/<chat>?attach=<bot>` addresses the *chat* in its username slot and names the bot in the
`attach` parameter instead — so the button matches this bot when that parameter is, and the
automatic scan surfaces such a button as this bot's the same way it surfaces a username match.
A kind that addresses neither a username nor a parameter at any bot — a boost, an invite, a
message link — never matches any bot, so a button of that kind is never treated as this bot's
by either an explicit target or the scan.

#### Scenario: Following a group button opens the conversation in the DM

- **WHEN** the bot posts a group message carrying a `t.me` start-link button and a user actor
  follows it
- **THEN** the user's private chat with the bot holds a `/start` message carrying the link's
  payload, and the handler registered for it ran

#### Scenario: The button has to be real

- **WHEN** a test follows a url that no message in scope carries
- **THEN** the call raises, naming the chat or the message it looked in

#### Scenario: A link to another bot is not followable

- **WHEN** the button deep-links to a different bot's username
- **THEN** the call raises rather than sending a `/start` to the bot under test

#### Scenario: The newest followable button is chosen

- **WHEN** no target is given and several messages carry deep-link buttons
- **THEN** the most recent followable link to this bot is the one followed

#### Scenario: An attachment-menu link matches by its parameter, not its address

- **WHEN** the button's url addresses a chat by username and carries `?attach=<bot>` naming
  this bot
- **THEN** the button is treated as this bot's — refused as an attachment-menu link, not as a
  link to a different bot — and the automatic scan surfaces it as a candidate

### Requirement: Only start links are followed, and the rest are refused by name

The toolkit SHALL classify every `t.me` / `telegram.me` / `tg://resolve` url, and every other
`tg://<host>` url, into the kind Telegram documents at https://core.telegram.org/api/links —
one policy per kind, not one bucket for "recognized" and another for "everything else". `start`
SHALL be the only followable kind, including a link with no query, which SHALL parse as a plain
start with no payload. A `start` payload with a non-empty value SHALL be honored alongside any
other query parameter, since a real client reads the parameter it recognizes and ignores the
rest; that precedence SHALL hold in either query order, so a link carrying both a non-empty
`start` and a Mini App, group or channel launch SHALL be followed as the start it also is. An
empty `start` SHALL NOT take this precedence, since it carries no value a real client could
have read as one — `?start=&startapp=y` SHALL classify as the `startapp` link it also is, not
as a bare start, while a bare `?start=` with nothing else in the query is still the plain start
it already was. The precedence SHALL need a real, non-empty `start` to take it, so one of those
kinds appearing alone is refused as before.

A query parameter Telegram documents as also being the companion of another format —
`startapp` and `startattach`, each of which also serves as the start parameter of a named-app
or named-chat attachment-menu link, and `text`, which a public username link may carry as a
prefilled draft alongside another parameter — SHALL NOT outrank the format that carries it:
`?startapp=x&text=y` SHALL classify as the Mini App link `startapp` names, not the draft `text`
would be alone, and `?appname=<name>&startapp=<param>` SHALL classify as the direct Mini App
link `appname` names, with `startapp` read as its parameter. A companion parameter appearing
alone in the query still classifies by the format it names.

Every other documented kind SHALL be refused with a message naming that kind and what a real
client does with it, rather than being replayed as a plain start or lumped into a generic
rejection: group, Mini App, channel and attachment-menu launches; a direct Mini App link and a
game-share link; an affiliate-referral link; a profile link; a prefilled-draft link; chat invite
links (including the legacy `joinchat` path and the `tg://join` form); a phone-number link,
told apart from an invite link by its all-digit tail rather than folded into the same kind; a
message link and its threaded and private-channel forms; a story link; a channel's web-preview
link (`t.me/s/<username>`), distinguished from a direct Mini App link despite sharing the
`t.me/<name>` shape; a share link; an invoice
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
real client never sends `/start` for a link its own payload makes invalid. The caller MAY opt
out of this validation, since the Bot API states the rule for what a bot should put in a link
but does not promise a client enforces it, and production bots do receive payloads outside it;
opting out SHALL replay the payload exactly as the button carries it, and SHALL NOT change
which kinds are followable — a `startapp` link opted out of payload validation is still refused
as a Mini App link, not silently followed as a start.

#### Scenario: A bare profile link replays as a plain start

- **WHEN** the button's url is `https://t.me/<bot>` with no query
- **THEN** following it sends `/start` with no payload

#### Scenario: An explicit non-empty start wins over a start-ish parameter beside it

- **WHEN** the button's url carries both a non-empty `start` and one of `startapp`,
  `startgroup` or `startchannel`, in either order
- **THEN** following it sends `/start` with the `start` payload rather than being refused

#### Scenario: An empty start does not win over a start-ish parameter beside it

- **WHEN** the button's url carries `?start=` with an empty value alongside `startapp`,
  `startgroup`, `startchannel`, `startattach` or `attach`, in either order
- **THEN** following it raises as that other kind, rather than sending a bare `/start`

#### Scenario: A companion parameter does not outrank the format that carries it

- **WHEN** the button's url carries a companion parameter (`startapp`, `startattach` or `text`)
  alongside a parameter of another documented format, in either order
- **THEN** following it raises as that other format, not as the companion's own kind

#### Scenario: Every documented format is refused as the format it is

- **WHEN** the button's url is one of the link forms https://core.telegram.org/api/links
  documents — a direct Mini App link, a message link, a story link, a share link, an invoice
  link, a boost link, a video-chat link, a business-chat link, a sticker-set link, a
  prefilled-draft link, an affiliate-referral link, a profile link, or a service link such as a
  proxy or language pack
- **THEN** following it raises, naming that kind and what a real client does with it, and — for
  an invoice or a boost link — pointing at the trigger (`pay()`, `pre_checkout_query()`,
  `boost()`) that models the underlying action instead

#### Scenario: A channel web-preview link is not mistaken for a Mini App

- **WHEN** the button's url is `t.me/s/<username>`, `t.me`'s own web preview of a channel's
  posts
- **THEN** following it raises naming it a channel web-preview link, not a direct Mini App link
  of a bot named `s`

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

#### Scenario: Payload validation can be dropped to reproduce what a client actually delivered

- **WHEN** the caller opts out of `start` payload validation and the button's payload is
  outside the deep-linking alphabet
- **THEN** the payload is replayed exactly as carried, and a kind other than `start` is still
  refused rather than made followable

#### Scenario: An unrecognized query is refused rather than guessed

- **WHEN** the button's url carries a query parameter none of the documented kinds define
- **THEN** following it raises, saying that what a real client would do with it is not
  simulated

#### Scenario: The scan skips what it cannot follow

- **WHEN** a keyboard carries both an unfollowable deep link and a real start link to this bot
- **THEN** the start link is followed; and when only unfollowable ones are present, the
  failure names each url and why it was rejected
