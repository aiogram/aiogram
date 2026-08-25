=======
Testing
=======

*aiogram* ships an integration testing toolkit: a stateful fake Telegram that your bot
talks to instead of the network. Updates go through the real
:class:`aiogram.dispatcher.dispatcher.Dispatcher`, so filters, middlewares, dependency
injection, FSM and Scenes all run exactly as they do in production, while every Bot API
call is applied to — and answered from — an isolated in-memory world.

.. code-block:: bash

    pip install aiogram[test]

Installing the extra is the only setup step: the fixtures are registered through a
``pytest11`` entry point, so no ``conftest.py`` boilerplate is needed.

.. warning::

    **This toolkit is a proof of concept.** Everything on this page — the module name, the
    fixture names, the blueprint and actor APIs, the world model and which Bot API methods
    it models — is subject to change, and may change incompatibly between releases while
    the design settles. Feedback on the shape of the API is exactly what it is for.

Quick start
===========

Point the ``bot_dispatcher`` fixture at your real dispatcher and start driving
conversations:

.. code-block:: python

    import pytest

    from aiogram import Dispatcher
    from my_bot.handlers import router


    @pytest.fixture
    def bot_dispatcher():
        dispatcher = Dispatcher()
        dispatcher.include_router(router)
        return dispatcher


    async def test_start_command(bot_user, bot_chat):
        await bot_user.send("/start")

        assert bot_chat.messages[-1].text == "Welcome!"

``bot_user`` is an actor bound to a chat, ``bot_chat`` is the live chat state, and
``bot_env`` is the environment they belong to. Every test gets a fresh world.

Declaring the world
===================

A :class:`aiogram.test.Blueprint` describes the participants. It holds no runtime state,
so it can be built once and shared at any scope — each test still materializes its own
independent world from it:

.. code-block:: python

    import pytest

    from aiogram.enums import ChatMemberStatus
    from aiogram.test import Blueprint


    @pytest.fixture(scope="session")
    def bot_blueprint():
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice", username="alice")
        bob = blueprint.add_user("Bob")
        blueprint.add_private_chat(alice)
        blueprint.add_supergroup(
            "Team",
            members={alice: ChatMemberStatus.ADMINISTRATOR, bob: ChatMemberStatus.MEMBER},
        )
        return blueprint

``Blueprint(default=...)`` takes a :class:`~aiogram.client.default.DefaultBotProperties`,
the same object a production bot is built with. World messages are bound to ``bot_env.bot``,
so its shortcuts — ``message.answer(...)``, ``message.reply(...)`` — resolve ``parse_mode``
and the rest of the defaults through it exactly as they would through the real bot. Passing
a blueprint that does not match the production ``Bot(default=...)`` is easy to miss, because
nothing raises: the mismatch only shows up as a wrong value in a call log assertion. Give
the blueprint the same defaults the bot actually runs with:

.. code-block:: python

    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    blueprint = Blueprint(default=DefaultBotProperties(parse_mode=ParseMode.HTML))

A user's own private chat with the bot opens on demand **when the user is the one acting**;
every other chat must be declared. Telegram lets any user open a DM with any bot — tapping a
``/start`` deep link does it as a side effect — so a blueprint that never called
``add_private_chat`` is not saying "this user has no private chat", only that the test did
not need to name it. Both ``bot_env.user(alice).send("/start")`` and a followed deep link
therefore work, and open a chat shaped exactly like a declared one. So does
``bot_env.chat(alice.id)`` on its own, for any id that names a **declared user** whose
private chat was not — every Telegram user can open one, so this accessor agrees with the
actor path (``bot_env.user(alice).chat``) instead of raising where that path already
succeeds. A *group*, on the other hand, is a place the bot was added to: ``.in_(chat)`` on a
chat nobody declared raises, because a bot cannot post into a chat it does not know, and so
does ``bot_env.chat(...)`` on any id that names neither a declared chat nor a declared user.

The bot's own calls open nothing. A real bot cannot write first — it may only answer a user
who wrote to it — so a test whose bot opens the conversation is describing something Telegram
would never allow, and there is no honest world state to invent for it.
``bot_env.bot.send_message(chat_id=alice.id, ...)`` into a private chat nobody declared
therefore raises :class:`aiogram.test.WorldLookupError`, listing the chats this world does
have, rather than a :class:`~aiogram.exceptions.TelegramBadRequest` the bot's own error
handling would swallow. Declare the chat with ``blueprint.add_private_chat(alice)``, open it
with ``bot_env.world.ensure_private_chat(alice)`` — it also accepts the user's id or an
already-resolved ``UserState`` — or have the user write first.

The handles returned by ``add_user`` / ``add_private_chat`` / ``add_group`` are how you
address participants later:

.. code-block:: python

    async def test_group_flow(bot_env, bot_blueprint):
        alice, bob = bot_blueprint.users
        team = bot_blueprint.chats[1]

        await bot_env.user(alice).in_(team).send("/report")

        assert bot_env.chat(team).messages[-1].text.startswith("Report")

A group bot's first move is almost always checking its own rights, so the bot's status in
a group-like chat is worth declaring rather than left at the default ``MEMBER``.
``add_group``, ``add_supergroup`` and ``add_channel`` accept ``bot_status``, and
``blueprint.bot`` can appear directly in ``members`` instead — two ways of saying the same
thing, so combining them raises rather than letting one silently shadow the other:

.. code-block:: python

    blueprint.add_supergroup("Team", bot_status=ChatMemberStatus.ADMINISTRATOR)

    # equivalent
    blueprint.add_supergroup("Team", members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR})

Either way, ``get_chat_member`` on the bot's own id reports the declared status, so a
handler that gates itself on its own rights takes the same branch it would in production.

A status says what a member *is*; ``set_member`` says what they may **do**. An
administrator declared without rights has the ordinary ones, and the interesting case —
"the bot is an admin but cannot delete messages, so warn the user" — is a declaration of
its own:

.. code-block:: python

    from aiogram.test import administrator_rights

    team = blueprint.add_supergroup("Team", bot_status=ChatMemberStatus.ADMINISTRATOR)
    blueprint.set_member(
        team,
        blueprint.bot,
        rights=administrator_rights(can_delete_messages=False),
    )
    blueprint.set_member(team, alice, permissions=ChatPermissions(can_send_messages=False))

``administrator_rights(**overrides)`` builds the ordinary administrator rights with the
overrides applied, so a nearly-ordinary admin is one line rather than a seventeen-field
literal. The mask it returns is not tied to a chat type: which rights a chat actually
*reports* is decided when the membership is read, where the chat type is known — the Bot
API reports ``can_post_messages`` only for channels and ``can_manage_topics`` only for
supergroups, and a right that cannot exist in a chat reads back as ``None`` there. So one
declaration is truthful in every chat, and stating a right explicitly never grants less
than staying silent would:

.. code-block:: python

    # In a channel, both of these report `can_post_messages is True`.
    posting = administrator_rights(can_post_messages=True)
    blueprint.set_member(channel, blueprint.bot, rights=posting)
    blueprint.set_member(channel, blueprint.bot, status=ChatMemberStatus.ADMINISTRATOR)

Passing ``rights`` or ``permissions`` implies the status that carries it
(administrator, restricted); an explicit ``status`` wins, and declaring both for one member
raises, since they belong to different statuses.

Triggering events
=================

Actors build a schema-valid :class:`aiogram.types.Update` and feed it to the dispatcher.
The trigger returns whatever the handler returned; keyword arguments are passed through
as handler dependencies:

.. code-block:: python

    await bot_user.send("/start")                      # message
    await bot_user.send("/report", repository=repo)    # + dependency injection
    await bot_user.edit(message, "corrected")          # edited_message
    await bot_user.click("answer:yes")                 # callback_query
    await bot_user.inline_query("search")              # inline_query
    await bot_user.join()                              # chat_member
    await bot_user.leave()                             # chat_member

``click`` resolves the button from a message the bot actually sent, so a renamed
``callback_data`` breaks the test instead of silently passing:

.. code-block:: python

    async def test_menu(bot_user, bot_chat):
        await bot_user.send("/menu")
        assert bot_chat.messages[-1].reply_markup is not None

        await bot_user.click("answer:no")

        assert bot_chat.messages[-1].text == "You chose no"

Forgetting ``.in_(chat)`` before ``click`` is an easy mistake, and it fails with the same
"no button here" message a genuine typo in ``callback_data`` would — unless the button
exists in some *other* chat this world knows, in which case the failure names that chat
instead of leaving the two indistinguishable:

.. code-block:: python

    await admin.in_(team).send("pick", fields={"reply_markup": keyboard})

    await admin.click("go")   # forgot `.in_(team)` — this clicks admin's private chat
    # WorldLookupError: No message in chat ... carries a button with callback_data='go';
    # a button with this callback_data exists in chat -100... ('Team') — bind the actor
    # with `.in_(...)`

Replying
--------

``send`` accepts ``reply_to``, sugar for ``fields={"reply_to_message": ...}``: pass the
``Message`` itself, or the id of one already stored in the actor's chat. ``reply()`` is the
same thing spelled as what it reads like:

.. code-block:: python

    await bot_user.send("question")
    question = bot_chat.messages[-1]

    await bot_user.reply(question, "answer")
    # equivalent: await bot_user.send("answer", reply_to=question)

    assert bot_chat.messages[-1].reply_to_message is question

Neither trigger returns the ``Message`` it sent — reach for ``actor.chat.messages[-1]``
right after the call, most of all when the next step replies to what was just sent:

.. code-block:: python

    await alice.send("question")
    await bob.reply(alice.chat.messages[-1], "first reply")
    await alice.reply(bob.chat.messages[-1], "second reply")

An explicit ``reply_to_message`` in ``fields`` still wins over ``reply_to``, matching every
other field ``fields`` overrides.

Deep links
----------

A group message often carries a button that deep-links back to the bot instead of a
``callback_data`` button — "Continue in DM" and similar patterns. ``follow_deep_link``
validates it with the same guarantee as ``click`` — the button must really be there — then
replays what tapping it actually causes: the user's client opens a private chat with the
bot and sends ``/start <payload>`` there.

.. code-block:: python

    async def test_continue_in_dm(bot_env, bot_blueprint):
        alice, team = bot_blueprint.users[0], bot_blueprint.chats[1]

        await bot_env.bot.send_message(
            chat_id=team.id,
            text="Tap to continue",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="Continue", url="https://t.me/test_bot?start=team-42"),
                ]],
            ),
        )

        await bot_env.user(alice).in_(team).follow_deep_link()

        assert bot_env.chat(alice.id).messages[-1].text == "/start team-42"

The private chat is opened if the blueprint never declared one — the general rule that a
user's own private chat opens on demand, applied here: a user reached through a group button
has a DM with the bot from the moment they follow the link.

``https://t.me/<username>?start=<payload>`` is recognized, along with its ``http://`` and
schemeless ``t.me/...`` forms, and ``tg://resolve?domain=<username>&start=<payload>``. A
bare profile link — ``https://t.me/<username>`` with no parameter — is followable too, and
replays as a plain ``/start``, because that is what tapping it sends. A link to a *different*
bot is not followable.

One documented format addresses a bot the other way round: an attachment-menu link addresses
the *chat* by username and names the bot in its ``attach`` parameter instead —
``t.me/<chat>?attach=<bot>`` opens the attachment menu of ``@<bot>`` in ``<chat>``. Such a
button still counts as this bot's — the scan surfaces it, and an explicit follow reaches the
kind's own refusal, rather than either treating ``<chat>`` as the addressed bot or skipping the
button as another bot's — because the parameter, not the username, is where its bot lives.

An explicit ``start`` **with a non-empty value** wins over a start-ish parameter sharing its
query, in either order: ``?start=team-42&startapp=abc`` is a followable start carrying
``team-42``. Telegram itself hands out links shaped that way — a Mini App button carries both,
so a client that cannot open the app still opens the bot — and a real client reads only the
parameter it recognizes. The precedence needs a real, non-empty ``start`` to take it, though:
``?startapp=abc`` on its own is still refused by name, and so is ``?start=&startapp=y`` — an
*empty* ``start`` carries no value a real client could have read as one, so the link is still
the ``startapp`` Mini App link it also is, not a bare ``/start``.

A parameter another format carries as its own companion never outranks the format that carries
it: ``?startapp=x&text=y`` is the Mini App link ``startapp`` names, not the draft ``text``
would be alone.

``start`` is the only followable kind. Every other format `Telegram documents
<https://core.telegram.org/api/links>`_ is refused with a message naming that format and
what a real client does with it, rather than being quietly downgraded to a plain ``/start``
or lumped into one generic rejection: ``startgroup`` and ``startchannel`` (a chooser — drive
that flow directly with ``add_bot()`` instead), ``startapp``, ``startattach`` and ``attach``;
a direct Mini App link (``t.me/<bot>/<short_name>``); message, story and share links; a
channel's web-preview link (``t.me/s/<username>``, ``t.me``'s own web page of a channel's
posts, not a Mini App despite the shared ``t.me/<name>`` shape); sticker- and emoji-set links;
game and referral links; a profile link; and Telegram's service links (a proxy, theme,
language pack, chat folder and the like). Two kinds point at the trigger that models the
action instead of merely naming it: an invoice link (``t.me/$<slug>``,
``tg://invoice?slug=...``) says to use ``pay()`` or ``pre_checkout_query()``, and a boost link
says to use ``boost()``. A prefilled-draft link (``?text=...``) is refused naming the text it
would have left sitting unsent in the composer, and pointing at ``send()`` with that same text
— tapping it never delivers anything to the bot until the user presses send. A phone-number
link (``t.me/+15551234567``) is told apart from a chat invite link (``t.me/+<hash>``) by its
all-digit tail, the same way Telegram's own clients tell them apart, so the refusal never calls
one the other. A ``tg://`` url whose host is not ``resolve`` — ``tg://join``, ``tg://boost``,
an app screen such as ``tg://settings`` — is still recognized as a Telegram link and refused by
the kind that host documents, never reported as "not a Telegram link" just because its host is
unfamiliar:

.. code-block:: python

    await bot_env.bot.send_message(
        chat_id=team.id,
        text="Boost us!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="Boost", url="https://t.me/boost/durov"),
            ]],
        ),
    )

    await bot_env.user(alice).in_(team).follow_deep_link("https://t.me/boost/durov")
    # WorldLookupError: 'https://t.me/boost/durov' is a boost link, which opens the boost
    # screen of a channel, not a bot deep link; only `t.me/<username>[?start=<payload>]`
    # and `tg://resolve?domain=<username>[&start=<payload>]` links can be followed here —
    # use `boost()` to deliver the `chat_boost` update instead

A ``start`` payload is validated before it is followed: Bot API deep linking allows 1-64
characters of ``A-Z``, ``a-z``, ``0-9``, ``_`` and ``-``, so a payload outside that alphabet —
too long, percent-encoded, non-Latin — is a link a real client would never have sent ``/start``
for. Following it raises naming the rule, rather than handing the handler a payload production
could not have produced. Pass ``validate_payload=False`` to drop that check and replay the
payload exactly as the button carries it: the Bot API states the rule but does not promise a
client enforces it, and production bots do receive payloads outside it — base64 padding
(``=``), dots, more than 64 characters — so this reproduces what such a client actually
delivers. The default stays strict, so a payload the bot itself built wrong is still named as
the bug it is.

Every update kind has a trigger
-------------------------------

No handler is unreachable from a test — there is a trigger for every variant of
:class:`aiogram.types.Update`, and a test in aiogram's own suite fails if a future Bot API
version adds one without a trigger:

.. code-block:: python

    await user.request_join()                # chat_join_request
    await user.chosen_inline_result("r-1")   # chosen_inline_result
    await user.shipping_query("order-1")     # shipping_query
    await user.pre_checkout_query("order-1") # pre_checkout_query
    await user.pay("order-1")                # a successful_payment message
    await user.purchase_paid_media()         # purchased_paid_media
    await user.boost()                       # chat_boost
    await user.remove_boost()                # removed_chat_boost
    await user.guest_message("hello")        # guest_message
    await user.manage_bot()                  # managed_bot
    await user.update_subscription()         # subscription

Two routing rules follow the chat rather than the trigger name, because that is how
Telegram itself decides:

* In a chat declared as a **channel**, ``send`` produces ``channel_post`` and ``edit``
  produces ``edited_channel_post``. The stored post carries no ``from_user``; it is
  attributed to the channel through ``sender_chat``, with the actor's name as
  ``author_signature``.
* ``join`` and ``leave`` change *this actor's* membership and produce ``chat_member``,
  while ``add_bot`` and ``remove_bot`` change the **bot's** and produce
  ``my_chat_member``. A bot that only registers ``my_chat_member`` correctly does not see
  the other.
* In a **group or supergroup**, ``join`` and ``add_bot`` also post the ``new_chat_members``
  service message a real join or add delivers alongside the membership update — see
  `Joining and leaving`_.

Answering queries
-----------------

A trigger that issues a query records it as outstanding, and the matching answer method
consumes it. Answering an id that was never issued — or answering the same query twice —
raises :class:`aiogram.exceptions.TelegramBadRequest` with Telegram's own wording, so the
"query is too old and response timeout expired" failure is testable:

.. code-block:: python

    async def test_button_is_acknowledged(env, user, chat):
        await user.send("/menu")

        await user.click("answer:yes")

        assert env.calls.count(AnswerCallbackQuery) == 1

If a call fails this way, the id did not come from a trigger. Answer the query your
handler actually received (``query.id``) rather than a literal, or declare the outcome
with an override when the query is not the thing under test.

Payments end to end
-------------------

The whole flow is three triggers, each answered with the id its own handler received:

.. code-block:: python

    @router.shipping_query()
    async def shipping(query: ShippingQuery, bot: Bot):
        await bot.answer_shipping_query(query.id, ok=True, shipping_options=[...])

    @router.pre_checkout_query()
    async def checkout(query: PreCheckoutQuery, bot: Bot):
        await bot.answer_pre_checkout_query(query.id, ok=True)

    async def test_payment(user, chat):
        await user.shipping_query("order-1")
        await user.pre_checkout_query("order-1")
        await user.pay("order-1")

        assert chat.messages[-1].successful_payment.invoice_payload == "order-1"

No step requires the one before it, because real bots selling digital goods skip the
shipping query entirely.

.. note::

    The order of a payment flow is not enforced, and no balance moves: ``pay`` posts the
    ``successful_payment`` message, it does not model Telegram's payment provider. Star
    balances and refunds remain record-only.

Asserting
=========

Two complementary views. The **world** shows what the chat now looks like:

.. code-block:: python

    assert len(bot_chat.messages) == 2
    assert bot_chat.messages[-1].text == "Done"
    assert bot_chat.pinned_message_ids == [5]
    assert bot_chat.member(user_id).status == ChatMemberStatus.KICKED

The **call log** shows what was requested, with bot-level defaults already resolved:

.. code-block:: python

    from aiogram.methods import AnswerCallbackQuery, SendMessage

    assert bot_env.calls.count(SendMessage) == 1
    assert bot_env.calls.last(SendMessage).parse_mode == "HTML"
    assert bot_env.calls.last(AnswerCallbackQuery).text == "Saved"
    assert bot_env.calls.count(DeleteMessage) == 0

Everything carries the bot
==========================

A real session parses every response with the bot in the validation context, which is what
lets you call a shortcut on whatever a method returned. The fake mounts every object the
same way, and it does so the moment the object *enters* the world rather than only on the
way out of a call. Three consequences, all of them things a test leans on:

**Results are usable, not just readable** — including everything nested inside them and the
items of a list result:

.. code-block:: python

    message = await bot_env.bot.send_message(chat_id=bot_chat.id, text="hi")
    await message.edit_text("bye")

    reply = await message.reply("re")
    await reply.reply_to_message.delete()  # nested objects are mounted too

    for admin in await bot_env.bot.get_chat_administrators(chat_id=bot_chat.id):
        await admin.user.get_profile_photos()  # so are the items of a list result

**So is anything the world holds**, whoever put it there — a message a *user* sent, which
no call ever returned, and a service message the bot's own call produced as a side effect:

.. code-block:: python

    await alice.send("hello")

    await bot_chat.messages[-1].answer("hi")            # a user's message is mounted
    await (await bot_chat.wait_for_message()).answer("hi")   # so is one a wait returned

    await bot_env.bot.set_chat_title(chat_id=group.id, title="Renamed")
    assert bot_chat.messages[-1].new_chat_title == "Renamed"  # and the service message

**A handler receives the world's own object, not a copy of it.** Updates are mounted before
they reach the dispatcher, which skips the JSON round-trip the dispatcher would otherwise
use to re-mount them — so identity survives the trip:

.. code-block:: python

    @router.message()
    async def handler(message: Message):
        seen.append(message)


    await alice.send("hello")
    assert seen[-1] is bot_chat.messages[-1]

An object that already carries a bot keeps it. That matters when a second ``Bot`` shares the
session (see `Bots that use a global Bot instance`_): objects the world already owns stay
mounted to ``bot_env.bot``, whose defaults are the ones the world was built with, instead of
being claimed by whichever bot happened to ask for them last.

**Your own objects stay yours.** Mounting only ever reaches things the world minted. A
``reply_markup``, a ``ChatPermissions`` or a ``BotCommand`` list you pass to a call is
*copied* on the way in, so the module-level constant a whole test file shares is never
bound to a bot and never left holding a disposed environment; the value objects the world
stores are copied again on the way out, so reading them back does not bind the world's own
state. Messages are the deliberate exception — a returned message *is* the one the chat
holds, and that identity is the point. The same applies to an ``Update`` you build once and
feed to two environments: the second one gets a copy, so its replies land in its own world,
and the message that copy carries is registered in the destination chat — otherwise that
chat would keep handing out message ids the incoming message already used.

One consequence is shared with production: the bot an object is mounted to is part of its
identity for pydantic, so an object the fake hands out never compares equal to an identical
one built inside the test — while the two print identically, since the repr hides the
binding. Compare the payload instead:

.. code-block:: python

    assert message.reply_markup.model_dump() == markup.model_dump()

A failing ``==`` between two such objects says so, so the puzzle only costs one run. What
the *world* stores is unbound, though, so an assertion against a declared constant works
there:

.. code-block:: python

    assert bot_env.chat(group.id).permissions == ChatPermissions(can_send_messages=False)

What the fake models
====================

Every method that produces a message stores one, and every method that changes a message
changes the stored one:

* **Sending** — :code:`sendMessage`, all the media methods, :code:`sendMediaGroup`, and
  also :code:`sendInvoice`, :code:`sendGame`, :code:`sendPaidMedia`,
  :code:`sendChecklist`, :code:`sendLivePhoto` and :code:`sendRichMessage`.
* **Editing** — text, caption, reply markup, media, live location and checklist, plus
  :code:`stopMessageLiveLocation`.
* **Moving** — :code:`forwardMessage`, :code:`copyMessage` and their batch forms. A
  forwarded message carries :code:`forward_origin`; a copy does not, which is how a test
  tells them apart.
* **Pinning** — :code:`pinChatMessage`, :code:`unpinChatMessage`,
  :code:`unpinAllChatMessages`.
* **Chat member administration**, the bot's own profile, forum topics, business
  connections and communities, as described in their own sections below.

A stored message carries the values its request actually stated, so
:code:`send_location(latitude=48.85, longitude=2.29)` produces a message whose
:code:`location` reports those coordinates rather than synthesized ones.

Every other Bot API method — including methods added by a future Bot API version — is
recorded and answered with a schema-valid result built from its declared return type, so a
handler never breaks just because a call was not configured.

.. note::

    The fake models the *shape* of Telegram, not its policy. Rate limits, permission
    matrices, media processing and message-age limits on editing are not simulated.

    In particular, media *content* is synthesized: sending a photo stores a
    :class:`aiogram.types.photo_size.PhotoSize` with a plausible file id, and no bytes are
    ever read. Only the scalar values a request states — coordinates, durations,
    dimensions, star counts, contact details — are carried through to the stored message.

.. note::

    :code:`sendInvoice` stores a message carrying an :class:`aiogram.types.invoice.Invoice`;
    it does not model a payment flow. Ephemeral methods such as :code:`sendMessageDraft`
    and :code:`sendRichMessageDraft` stay record-only, matching Telegram, which does not
    persist them either.

A few methods have nothing to mutate but a useful answer, so they are drawn from the world
rather than synthesized: :code:`sendChatAction` rejects an unknown chat and otherwise
returns ``True``, :code:`getFile` echoes the ``file_id`` it was asked for so a download
path can be correlated, :code:`createInvoiceLink` returns a unique link, and
:code:`getUserPersonalChatMessages` reads from that user's private chat.

Sticker sets
============

A pack the bot builds is stored, so the check-before-you-write branch is testable:

.. code-block:: python

    async def test_adds_until_full(env, owner):
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name="my_pack_by_test_bot",
            title="My pack",
            stickers=[InputSticker(sticker="file-1", format="static", emoji_list=["🐱"])],
        )

        pack = await env.bot.get_sticker_set(name="my_pack_by_test_bot")

        assert len(pack.stickers) == 1

Adding, deleting, replacing, renaming and deleting the set all follow, and
``blueprint.add_sticker_set("my_pack_by_test_bot", stickers=3)`` declares a pack that
already exists. Replacing keeps the sticker's position, as the Bot API describes it.

The mistakes a pack bot makes raise: a name already taken, a set that does not exist, and a
sticker the set does not contain. Note that :code:`deleteStickerFromSet` names no set — the
sticker identifies one, and a sticker in no set at all raises.

:code:`uploadStickerFile` mints a stable id the set methods can reference. It registers no
content, deliberately unlike a document upload: a pack bot puts a sticker in a set and never
downloads it back, so downloading one raises.

.. note::

    No image data exists — a sticker is an object with a file id and nothing behind it.
    Telegram's pack rules are not enforced either: no 120-sticker limit, no format
    compatibility, no ``_by_<bot_username>`` naming convention. The per-sticker attribute
    setters — emoji list, keywords, mask position, position in set, and both thumbnail
    setters — stay :ref:`record-only <what-stays-record-only>`, because nothing reads them
    back.

Stars and gifts
===============

A star payment credits the bot, and the charge is recorded — so a handler refunds the id it
was actually given rather than one the test invented:

.. code-block:: python

    @router.message(F.successful_payment)
    async def paid(message: Message, bot: Bot):
        if not in_stock(message.successful_payment.invoice_payload):
            await bot.refund_star_payment(
                user_id=message.from_user.id,
                telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
            )


    async def test_refunds_when_out_of_stock(env, user):
        await user.pay("sold-out", total_amount=250)

        assert (await env.bot.get_my_star_balance()).amount == 0

Refunding a charge twice, or one that was never paid, raises. So does cancelling a
subscription for an unknown charge. Declare a starting balance with
``blueprint.set_star_balance(1000)`` when a test should not have to earn its stars first.

The balance is always computed from the recorded transactions, so it cannot disagree with
them — the same rule poll counts and reaction counts follow.

Gifts are owned inventory. ``getAvailableGifts`` returns a small **fake but stable**
catalogue, so ``gifts[0].id`` is the same on every run:

.. code-block:: python

    gifts = await bot.get_available_gifts()
    await bot.send_gift(gift_id=gifts[0].id, user_id=user_id)

    owned = await bot.get_user_gifts(user_id=user_id)
    assert owned.total_count == 1

Sending spends from the balance; converting a gift returns its stars; transferring moves it
to another owner; upgrading marks it unique. ``blueprint.add_owned_gift(user)`` declares a
gift somebody already has.

.. note::

    Three deliberate limits. Business bot rights (``can_convert_gifts_to_stars`` and
    friends) are **not** enforced, consistent with the toolkit enforcing no rights
    anywhere. Telegram's star economics — commission, payouts, the settlement hold — are
    not modeled; the ledger only counts stars in and out. And **affordability is not
    checked**: sending a gift you cannot pay for drives the balance negative rather than
    failing, because a negative balance is visible to a test while a silent rejection is
    not. Declare the rejection with an override if that is the branch under test.

Files and downloads
===================

A file the bot uploads with :class:`aiogram.types.input_file.BufferedInputFile` can be
downloaded again in the same test, with no setup — the upload registers the bytes it
carried:

.. code-block:: python

    async def test_echoes_the_document(env, chat, user):
        message = await env.bot.send_document(
            chat_id=chat.id,
            document=BufferedInputFile(b"report", filename="report.txt"),
        )

        assert await env.bot.download(message.document, destination=io.BytesIO()) is not None

For content the bot did not upload — a document a *user* sent, which the bot then downloads
and processes — declare it on the blueprint:

.. code-block:: python

    blueprint.add_file("incoming-id", pathlib.Path("fixtures/report.csv").read_bytes())

    async def test_parses_the_upload(env, user):
        await user.send("here you go", fields={"document": Document(file_id="incoming-id", ...)})

        ...  # the handler downloads "incoming-id" and gets the fixture's bytes

Downloading content the environment does not have **raises**
:class:`aiogram.test.errors.NoFileContentError`, naming the file id and how to supply it.
It does not hand back empty bytes: ``b""`` is indistinguishable from a genuinely empty
file, so a bot whose "no content" branch is wrong would pass every test.

.. note::

    The fake never touches the filesystem or the network, so
    :class:`aiogram.types.input_file.FSInputFile` and
    :class:`aiogram.types.input_file.URLInputFile` are **not** read — sending one uploads
    nothing, and downloading it afterwards raises. Declare the content instead.

    :code:`getFile` deliberately stays forgiving and succeeds for an id with no content: a
    bot often reads the path or size and never downloads. Only the download itself fails.

.. _what-stays-record-only:

What stays record-only
======================

Most of the Bot API is modeled, and the rest is not an oversight. These surfaces are
recorded and answered but deliberately **not** modeled, because for each of them the
recorded call is the whole useful assertion:

.. list-table::
    :header-rows: 1
    :widths: 30 70

    * - Surface
      - Why not
    * - Ephemeral messages and drafts
      - Telegram does not persist them either, so there is no state to read back.
    * - Managed bots
      - A second bot-identity concept that nothing else in the world reads.
    * - Verification badges
      - No field surfaces them.
    * - Profile and chat photos
      - Media processing is out of scope. Note that *deleting* a chat photo is modeled,
        because that is a state transition.
    * - Webhook configuration and :code:`getUpdates`
      - The toolkit drives ``feed_update`` directly and never runs either transport.
    * - Suggested posts
      - Would need a post lifecycle and two service messages to mean anything.
    * - Telegram Passport
      - A pure notification with no reader.
    * - Mini-app and web-app handoffs
      - The identifiers they exchange have no anchor in the world.
    * - Sender-chat bans
      - :code:`getChat` never exposes them, so a ban set would be write-only.
    * - Per-sticker attributes and thumbnails
      - Written, never read back.
    * - :code:`close` and :code:`logOut`
      - Rejecting calls after a logout is policy, not shape.
    * - Game scores
      - A score table nothing else consults.

Calling any of them still works — the call is recorded and answered with a schema-valid
result — and :meth:`aiogram.test.BotTestEnvironment.on` still overrides it. What you do not
get is world state changing as a result.

Deferred, not refused
---------------------

These clusters are *candidates*: coherent enough to model, waiting on someone needing them.
If one of them is what stands between you and a test, that is worth reporting — it is the
difference between "no" and "not yet":

* **Stories** — posting, editing and deleting against a story registry.
* **Business account profile** — name, username and bio on a connected account.

When a call fails
=================

Two different things can go wrong, and they are deliberately different exceptions.

A call the real Bot API would have refused fails the way it fails in production: a
:class:`aiogram.exceptions.TelegramBadRequest` carrying Telegram's own wording. Forwarding a
message that is not there, demoting the chat owner, stopping a poll that is already closed,
answering a query twice — bot code legitimately catches those, and a test of that ``except``
branch is a real test:

.. code-block:: python

    with pytest.raises(TelegramBadRequest, match="message to forward not found"):
        await bot_env.bot.forward_message(chat_id=chat.id, from_chat_id=chat.id, message_id=999)

A gap in the *test's own setup* does not. Asking for a user, chat, sticker set, poll or
business connection the blueprint never declared raises
:class:`aiogram.test.WorldLookupError`, and nothing converts it — it propagates out of the
call the bot made and fails the test with a message that says what to declare:

.. code-block:: python

    aiogram.test.WorldLookupError: User 999999 is not declared in the blueprint

A chat the bot addresses is on that list too. Any outbound call naming a chat this world does
not have — ``send_message``, ``ban_chat_member``, ``get_chat`` — raises the same way,
enumerating the chats that *are* declared and pointing at ``add_private_chat`` and its
siblings, or at ``env.world.ensure_private_chat(...)``.

That distinction is the whole reason there are two types. Reporting a missing declaration as
a Bad Request would hand it straight to the bot's own error handling, which would swallow it
and quietly exercise the wrong branch — the test would pass while testing nothing. The chat
case is where that bites hardest: "chat not found" is the branch a bot writes for the user
who blocked it, so a missing declaration used to run the blocked-user path and pass while
asserting on it. A test that genuinely wants that branch declares the refusal instead of
starving the world of a chat:

.. code-block:: python

    bot_env.on(SendMessage).raises(TelegramBadRequest, "Bad Request: chat not found")

The same goes for the few things the fake genuinely cannot model, such as editing a message
by ``inline_message_id``: those raise loudly rather than pretending Telegram refused.

Reaching into the world directly — ``chat.topic(999)``, ``chat.require_message(999)`` — is
outside any call, so there is nothing to convert the refusal into: those raise
:class:`aiogram.test.ApiRejection`, the type the environment turns into a Bad Request when
the bot is the one asking.

Overriding results and simulating failures
==========================================

.. code-block:: python

    from aiogram.exceptions import TelegramForbiddenError
    from aiogram.methods import GetChatMember, SendMessage


    async def test_blocked_user(bot_env, bot_user):
        bot_env.on(SendMessage).raises(TelegramForbiddenError, "Forbidden: bot was blocked")

        await bot_user.send("/start")  # your error handling runs for real


    async def test_admin_only(bot_env, bot_user):
        bot_env.on(GetChatMember).returns(some_administrator)

        await bot_user.send("/ban")

Overrides take precedence over everything else and can be limited to a number of calls
with ``times=``, so consecutive calls can return different outcomes. Errors are raised as
the framework's own :mod:`aiogram.exceptions` types, through the same code path a real
response takes.

A declared result stays the test's own: each call is answered with a fresh copy of it, the
way a real response is parsed anew every time. So ``some_administrator`` above can be a
module-level object shared by the whole suite — the call cannot mutate it, and it never
ends up holding a reference to a bot from an environment that is already gone.

Targeting one call among several
---------------------------------

A bare ``bot_env.on(SendMessage)`` answers *every* ``sendMessage``, which is not enough once a
bot reacts to one event by messaging several chats — a game engine telling the group and
every player at once. ``bot_env.on`` also takes keyword arguments, each an equality test on a
field of the **resolved** method — after bot-level defaults such as ``parse_mode`` are
filled in — and they are AND-ed:

.. code-block:: python

    bot_env.on(SendMessage, chat_id=alice.id).raises(TelegramForbiddenError, times=1)
    bot_env.on(SendMessage, chat_id=bob.id).raises(TelegramForbiddenError, times=1)

Both rules stand at once. A message to a *third* chat in between consumes neither —
**a rule whose matcher rejects a call is skipped without its ``times`` budget moving** — so
"these two players blocked the bot" no longer depends on which order the engine happens to
message them in, the way a single untargeted ``.raises(times=1)`` would.

``.where(predicate)`` is the escape hatch for anything a field equality cannot say — a
substring of the text, a particular button, a chat id drawn from a set — and it composes
with the keyword filters:

.. code-block:: python

    bot_env.on(SendMessage).where(lambda call: "night" in (call.text or "")).raises()

Narrowing a builder with ``.where`` (or declaring a further keyword filter) after
``.returns()``/``.raises()`` was already called on it only narrows what is declared *after*
that point — an earlier declaration keeps the matcher it had when it was made. A field the
method does not have raises ``TypeError`` immediately, naming the fields that do exist,
rather than registering a rule that can never match — the misspelling would otherwise only
surface much later, as "the bot sent the message it was supposed to fail to send".

Several rules for one method are tried oldest first, and the first whose matcher accepts
the call wins:

.. code-block:: python

    bot_env.on(SendMessage).returns("general")
    bot_env.on(SendMessage, chat_id=alice.id).returns("specific")

    await bot_env.bot.send_message(chat_id=alice.id, text="hi")  # "general" — registered first

``bot_env.on(...)`` returns a **handle** as well as a builder: ``.cancel()`` withdraws exactly
the rules that call registered, leaving every other rule alone, and the handle works as a
context manager, scoping an override to one block:

.. code-block:: python

    with bot_env.on(SendMessage, chat_id=alice.id).raises(TelegramForbiddenError):
        await bot_user.send("/start")
    # from here on the bot can message alice again

The player blocked the bot
---------------------------

``bot_env.blocked(chat_id)`` is that scenario spelled out directly — despite the keyword's
name, it accepts a bare id, a ``ChatSpec``/``ChatState`` or a ``UserSpec``/``UserState``, since
a user's own private chat is addressed by their id. It covers more than ``sendMessage``: a real
block stops *every* call that delivers into that chat —
photos, chat actions, copies, forwards, and any future ``send*``/``copy*``/``forward*`` method
a Bot API bump adds, via :data:`aiogram.test.DELIVERY_METHODS` — **and** every call that acts
on what is already in that chat instead of delivering into it: the ``editMessage*`` family,
``stopMessageLiveLocation``, ``stopPoll``, ``setMessageReaction``, and
``pinChatMessage``/``unpinChatMessage``/``unpinAllChatMessages``. The full set a block stops is
:data:`aiogram.test.BLOCKED_METHODS`, which extends ``DELIVERY_METHODS`` with those additions:

.. code-block:: python

    from aiogram.test import BLOCKED_BY_USER

    with bot_env.blocked(chat_id=alice.id):
        await bot_user.send("/start")   # the group still gets its message
        with pytest.raises(TelegramForbiddenError, match=BLOCKED_BY_USER):
            await bot_env.bot.send_message(chat_id=alice.id, text="your role")

    await bot_env.bot.send_message(chat_id=alice.id, text="again")  # alice is unblocked again

:data:`~aiogram.test.BLOCKED_BY_USER` is the same string ``blocked()`` raises with by default,
so a test asserts against the constant instead of a copy-pasted literal that could drift from
it.

``deleteMessage``/``deleteMessages`` are a deliberate exclusion from ``BLOCKED_METHODS``: the
Bot API states their limits in terms of message age and administrator rights, not of
reachability, and a bot dropping its own leftovers is not delivering anything — guessing a 403
there would fail a cleanup path in tests that succeeds in production, the more expensive
mistake of the two. A test that knows better declares it in one line:
``bot_env.on(DeleteMessage, chat_id=alice.id).raises(TelegramForbiddenError)``.

Some methods name the blocked party as ``user_id`` rather than ``chat_id`` — ``sendGift`` is
the one that forces the question, since a bot thanking a user reaches for ``user_id`` with no
``chat_id`` in sight. ``blocked(...)`` still catches it: the recipe registers a rule on every
addressing field a blocked method actually has, ``chat_id`` **or** ``user_id``:

.. code-block:: python

    with bot_env.blocked(chat_id=alice.id), pytest.raises(TelegramForbiddenError):
        await bot_env.bot.send_gift(gift_id="gift-1", user_id=alice.id)

``chat_id`` (and its siblings ``from_chat_id``, ``sender_chat_id``) is resolved through the
world before comparison, on both a block and a plain ``env.on(...)`` filter alike, so
``'@alice'`` and Alice's numeric id compare equal: a block declared with the numeric id still
catches a call the bot addresses as ``chat_id="@alice"``, and a filter declared with
``chat_id="@alice"`` still catches a call addressed by the numeric id.

Two players can be blocked independently — ``with bot_env.blocked(chat_id=alice.id),
bot_env.blocked(chat_id=bob.id):`` — which is the case a single untargeted
``bot_env.on(SendMessage).raises(times=1)`` could not express, since it would fail whichever of
them the engine happens to message first. Unlike a plain ``.raises()``, ``bot_env.blocked``
carries no ``times`` budget: a blocked user stays blocked for as long as the block is in
force rather than for exactly one call, and it can be cancelled by hand instead of scoped
with ``with``:

.. code-block:: python

    block = bot_env.blocked(chat_id=alice.id)
    ...
    block.cancel()

Pass ``message=`` to get a different refusal than a block — ``"Forbidden: user is
deactivated"``, for instance — through the same recipe.

An override that never fires
-----------------------------

A misspelled field filter — ``env.on(SendMessage, chat_di=alice.id)`` — is caught immediately
if the field does not exist at all, but not if it does and simply never matches anything: a
chat id one digit off, a ``where`` predicate that is subtly wrong, a rule declared after the
call it meant to intercept. The rule sits in the registry doing nothing, the bot behaves as if
it were never declared, and the test fails somewhere else entirely — "the bot sent the message
it was supposed to fail to send."

``bot_env.assert_overrides_consumed()`` names every declared override that never answered a
call:

.. code-block:: python

    with bot_env.blocked(chat_id=alice.id):
        await bot_user.send("/broadcast")
    bot_env.assert_overrides_consumed()

It is opt-in rather than automatic teardown, because a test that declares a rule for a path it
does *not* expect to be taken is a perfectly good test — proving the bot never went there. The
same listing is appended to every ``wait_for`` and ``wait_for_message_in`` timeout, since a
never-matched override is the single most common reason a message a test is waiting for never
arrives.

Recording happens before an override answers
-----------------------------------------------

:attr:`~aiogram.test.BotTestEnvironment.calls` records a call **before** any override —
``bot_env.on(...)``, ``bot_env.blocked(...)``, or the modeling and synthesis they take precedence
over — is consulted. That ordering is what lets a test assert both halves of a refusal: that
the bot *tried* to reach the right addressee, and that it *coped* with being refused.

.. code-block:: python

    with bot_env.blocked(chat_id=alice.id), pytest.raises(TelegramForbiddenError):
        await bot_env.bot.send_message(chat_id=alice.id, text="your role")

    assert bot_env.calls.last(SendMessage).chat_id == alice.id
    assert bot_env.calls.last(SendMessage).text == "your role"

Routing diagnostics
====================

A trigger returns *a* result, not the route the update actually took, so an update
swallowed by a middleware, one caught by a catch-all logging handler, and one that reached
the handler under test can all come back looking the same — and the test only notices
minutes later, as a ``wait_for`` that timed out with nothing to say about why.
:attr:`~aiogram.test.BotTestEnvironment.last_route` is where the most recently fed update
actually went:

.. code-block:: python

    await bot_user.send("/join")

    assert bot_env.last_route.handled
    assert bot_env.last_route.router == "membership"

:meth:`~aiogram.test.BotTestEnvironment.assert_handled_by` is the assertion spelled
directly, matched against ``module.qualname`` as a substring — so ``"on_join"`` and
``"handlers.membership.on_join"`` both work — and it fails naming where the update actually
went, exception included, rather than only "not handled":

.. code-block:: python

    bot_env.assert_handled_by("on_join")
    # AssertionError: Expected the last trigger to be handled by 'on_join', but its 1
    # update(s) went here:
    # update id=... (message) was handled
    #   handler: handlers.other.log_everything
    #   router:  fallback

Reach for this whenever an update "went nowhere" and the reason is not obvious: **handled**
and **handler is not None** answer different questions. ``handled`` is aiogram's own
definition — the dispatcher returned something other than ``UNHANDLED`` — which a
middleware that returns ``None`` without calling the next one already satisfies, so it is
``handler`` that says whether anything actually ran:

.. code-block:: python

    assert bot_env.last_route.handled is True   # a middleware answered without calling on
    assert bot_env.last_route.handler is None   # ...but no handler ever ran

``exception`` is captured **where it was raised**, not where it surfaced — including a
handler exception the bot's own ``@dp.error()`` handler goes on to swallow, which otherwise
leaves a test staring at a missing reply with no clue that a handler ever raised at all:

.. code-block:: python

    assert bot_env.last_route.handler and "boom" in bot_env.last_route.handler
    assert isinstance(bot_env.last_route.exception, RuntimeError)

One thing a test does is often more than one update. A real join delivers a ``chat_member``
transition *and* the group's own ``new_chat_members`` service message (see `Joining and
leaving`_), and a bot that handles the first and ignores the second used to make
``bot_env.assert_handled_by("on_user_joined")`` fail — "the last update" was the service
message nobody claimed, even though the join was handled correctly. So ``last_route``,
``routes`` and ``assert_handled_by`` all reason about a **trigger scope**, one thing the test
did, rather than one update — which is what lets a multi-update trigger like ``join()`` /
``add_bot()`` assert cleanly with no ceremony at all:

.. code-block:: python

    await member.join()  # feeds chat_member, then new_chat_members

    bot_env.assert_handled_by("on_user_joined")  # matches whichever update the bot claimed

A test writing a multi-update helper of its own opens the same scope explicitly with
:meth:`~aiogram.test.BotTestEnvironment.trigger`:

.. code-block:: python

    with bot_env.trigger():
        await alice.send("/deal")
        await bob.send("/deal")
    bot_env.assert_handled_by("on_deal")   # scans both updates

:attr:`~aiogram.test.BotTestEnvironment.routes` is every record of the current scope, in the
order routing finished. :attr:`~aiogram.test.BotTestEnvironment.last_route` is the **newest
handled** record among them, falling back to the newest record of any kind only when nothing
in the scope was handled at all — the ordering that lets the join example above report the
update the handler actually claimed, rather than whichever of the two Telegram happens to
deliver last, while a scope nothing reacted to still reports "NOT handled" instead of hiding
behind an earlier, unrelated success. ``assert_handled_by`` scans **every** record of the
scope, not only the newest, and its failure message dumps all of them — including any
exception raised and swallowed along the way.

Nesting is counted, so a helper that opens its own ``trigger()`` inside a wider one does not
close the outer scope early. A bare ``feed`` — a plain ``await bot_user.send(...)`` outside any
explicit ``trigger()`` block and not itself fed from inside a running handler — opens a scope
of its own, which is what keeps the common one-update case free of ceremony. ``routes`` is
empty and ``last_route`` is ``None`` until the first update is fed.

Finite state machine
====================

The environment installs a fresh :class:`aiogram.fsm.storage.memory.MemoryStorage` per
test, so FSM state is isolated even when your dispatcher is configured with Redis. You
can read the resulting state, or arrange one up front to skip the earlier steps:

.. code-block:: python

    async def test_registration(bot_env, bot_user, bot_blueprint):
        state = bot_env.state(bot_blueprint.users[0])
        await state.set_state(Registration.age)
        await state.update_data(name="Bob")

        await bot_user.send("41")

        assert bot_chat.messages[-1].text == "Registered Bob, 41"
        assert await state.get_state() is None

Under a topic-aware :class:`aiogram.fsm.strategy.FSMStrategy`, or on a business
connection, the storage key includes the thread and the connection — pass them, or the
context you get back is a *different* key than the one the dispatcher used:

.. code-block:: python

    state = bot_env.state(alice, team, topic=support)
    state = bot_env.state(alice, chat, business_connection=connection)

    # Or let the actor's own binding fill both in:
    state = actor.state()

Bots with background tasks
==========================

A bot that runs an engine of its own — timers, a scheduler, a game loop — keeps changing
the world after a trigger has already returned, while every assertion on the world is a
snapshot taken the instant it runs. ``wait_for`` and ``wait_for_message`` close that gap:
both poll, yielding to the event loop between checks so the bot's background tasks get a
chance to run.

.. code-block:: python

    await env.wait_for(lambda: game.mode is Mode.NIGHT, "night to begin")

    message = await env.chat(group).wait_for_message(lambda m: m.reply_markup is not None)
    await message.answer("go on")  # whatever a wait returns is mounted, like any result

:meth:`aiogram.test.BotTestEnvironment.wait_for` re-checks any predicate — synchronous or
returning an awaitable — until it produces something truthy, and hands that value back, so
it can fetch as well as test. :meth:`~aiogram.test.world.ChatState.wait_for_message` is the
specialized form for the case that dominates these tests: something the trigger did not
await is expected to post into a chat. A topic waits the same way, over its own filtered
view of the chat's messages, so a message posted into a sibling topic never satisfies it::

    message = await env.topic(forum, support).wait_for_message(lambda m: m.text == "done")

What a wait is *for* is the second **positional** argument of both, as in the first example
above, rather than a keyword — these are written with lambdas, and for a lambda that
description is the only thing a failure message has to go on, so saying it should cost no
ceremony::

    await bot_chat.wait_for_message(lambda m: m.text == "Dawn", "the dawn announcement")

A message that is already there satisfies the wait immediately — the predicate is matched
against every message the view holds, not only the ones arriving after the call — so a test
never has to race the send it is waiting for. When more than one matches, the one with the
highest ``message_id`` is returned: the newest as Telegram numbers them, rather than
whichever the list happens to hold last. A chat is normally in id order anyway, but
"normally" is not something a test can act on, and the one path that could break it is a
message registered from another environment — exactly the case where a test asking for the
newest reply must not silently get a stale one.

Dumping what the bot said instead
----------------------------------

A general ``wait_for`` can only report the condition it was given, and the condition is a
lambda over the bot's own state — while the answer to "why did it never become true" is
almost always in what the bot said *instead*. ``watch=`` names one chat or topic to dump, or
any iterable of them, and each is appended to the timeout message the way
``wait_for_message``'s own failure already renders one:

.. code-block:: python

    await env.wait_for(lambda: game.mode is Mode.NIGHT, "night to fall", watch=group)
    # WaitTimeoutError: Timed out after 5.0s waiting for night to fall.
    # In chat -100...: The chat holds 3 message(s):
    #   #1 'Waiting for players...'
    #   ...

``watch=`` and ``wait_for_message_in``'s ``chats=`` speak one shared vocabulary, resolved by
:meth:`~aiogram.test.BotTestEnvironment.as_views`: a blueprint's ``ChatSpec``/``TopicSpec``
declaration, a live ``ChatState``/``TopicState``, or a bare chat id — one of them on its own,
or any iterable of them mixed freely. A timeout also appends a listing of any override this
environment declared that never answered a call — see `An override that never fires`_ — since
that is the single most common reason a message a wait is looking for never arrives.

Waiting for a broadcast
-------------------------

A bot that fans one event out to many chats — every player gets the night keyboard, every
subscriber gets the digest — is otherwise tested by awaiting each chat's own
``wait_for_message`` in turn, which is slower (the timeouts are serial) and much worse at
failing: the first chat that never got its message ends the wait, and the rest are never
even looked at, so a systematic failure reads as one unlucky chat.
:meth:`~aiogram.test.BotTestEnvironment.wait_for_message_in` polls **every** named chat
together and returns once all of them hold a match:

.. code-block:: python

    player_ids = [alice.id, bob.id, carol.id]

    keyboards = await env.wait_for_message_in(
        player_ids, lambda m: m.reply_markup is not None, "the night keyboard"
    )
    assert keyboards[alice.id].reply_markup is not None

``chats`` accepts the same vocabulary as ``watch=`` above — declarations, live chat and topic
states, bare ids, one or an iterable, mixed freely — so a broadcast into one thread of a forum
is expressible too, and the newest match per chat wins, exactly as a single
``wait_for_message`` picks it. A predicate that raises on a message counts as "no match" for
that message rather than failing the wait, and — again as the single-chat wait does — what it
raised is reported once the wait gives up, per chat. A timeout names only the chats that are
still missing a match, not the ones that already have one — the difference between "somebody
didn't get it" and a readable diagnosis — and, as with any wait, appends a listing of any
override that never fired.

How long a wait runs before giving up is set once, on the environment — override the
``bot_env_wait_timeout`` fixture to say it for a whole suite, the same way ``bot_blueprint``
and ``bot_dispatcher`` are overridden:

.. code-block:: python

    @pytest.fixture
    def bot_env_wait_timeout():
        return 1.0

That is what :class:`~aiogram.test.BotTestEnvironment`'s own ``default_wait_timeout``
parameter is for — the plugin's ``bot_env`` fixture just reads ``bot_env_wait_timeout`` and
passes it along, so a project using the fixtures never has to reconstruct ``bot_env`` from
scratch just to change one number. Building a :class:`~aiogram.test.BotTestEnvironment`
directly, outside the fixtures, still passes it the same way::

    BotTestEnvironment(blueprint=blueprint, dispatcher=dispatcher, default_wait_timeout=1.0)

``default_wait_timeout`` is the single place for it: ``wait_for``, every chat's
``wait_for_message`` and every topic's read it, so a bot whose background work is slow — or a
suite that wants a fast failure instead of a five-second pause per timing bug — says so once
rather than on every call. It defaults to five seconds, and an explicit ``timeout=`` on a
single call still wins over it.

Both give up with
:class:`aiogram.test.WaitTimeoutError`, a :class:`TimeoutError` whose message names what
was awaited and enumerates the messages of the chat or topic it waited in, so a failure
shows what actually arrived
instead of just "timed out"; neither overshoots its ``timeout``, whatever ``interval`` it
was given.

The messages a predicate is matched against come in every shape, so one that raises on a
message counts as "no match" rather than failing the wait.
``lambda m: m.text.startswith("Night")`` would otherwise die on the first service message,
whose ``text`` is ``None``, having nothing to do with what the test is waiting for. The
exceptions are not swallowed: if the wait times out, the failure message reports what the
predicate raised and on which message, so a predicate that is simply wrong still fails with
its real cause.

A real engine's own ``sleep()`` calls make a test that waits on them real-time slow —
``wait_for`` removes the boilerplate of polling, not the wall-clock time a fifteen-second
game phase actually takes. This proof of concept deliberately ships no fake clock of its
own, but a fake clock is not something the toolkit needs to own: nothing in the fake world
touches the network or the wall clock itself, so a library that virtualizes the event
loop's own clock composes underneath it without conflict.

`looptime <https://pypi.org/project/looptime/>`_ is one such library — a pytest plugin
that makes ``asyncio.sleep`` and ``loop.call_at`` resolve the instant their deadline is
reached, with no real delay:

.. code-block:: bash

    pip install looptime

No conftest is required — ``looptime`` registers itself the same way the toolkit does, and
marking one test is enough to run it on the fake clock:

.. code-block:: python

    import asyncio

    import pytest

    from aiogram import Bot, Dispatcher, Router

    router = Router()


    @router.message()
    async def start_night(message, bot: Bot) -> None:
        asyncio.create_task(run_night_phase(bot, message.chat.id))


    async def run_night_phase(bot: Bot, chat_id: int) -> None:
        await asyncio.sleep(15)  # the engine's own hardcoded sleep
        await bot.send_message(chat_id=chat_id, text="Night falls.")


    @pytest.fixture
    def bot_dispatcher() -> Dispatcher:
        dispatcher = Dispatcher()
        dispatcher.include_router(router)
        return dispatcher


    @pytest.mark.looptime
    async def test_night_phase_begins(bot_env, bot_user, bot_chat):
        await bot_user.send("/start")

        message = await bot_chat.wait_for_message(
            lambda m: m.text == "Night falls.",
            timeout=20.0,
            interval=0.5,
        )

        assert message.text == "Night falls."

On a real clock this test takes just over fifteen seconds. Verified under ``looptime`` it
ran in under 20 milliseconds — a background task's fifteen-second ``asyncio.sleep``
resolves the moment the virtual clock reaches it rather than fifteen real seconds later,
and the wait's own deadline, built on the same event loop's ``loop.time()``, keeps its
timing promises unchanged: a wait that should time out still does, and still does so in
milliseconds even when ``timeout`` is generously large.

``interval=0.5`` above is deliberate, not decoration. Both waits still poll by sleeping
``interval`` seconds between checks, and each of those sleeps is a real iteration of the
event loop even under ``looptime`` — the clock jumps, the loop's own bookkeeping does not.
Left at the default ``interval=0.01`` against this same fifteen-second wait, that is
fifteen hundred iterations, and their per-iteration overhead stopped being negligible: the
identical scenario measured close to a full second of real time instead of milliseconds.
Pick an interval that matches the coarseness of what a test is waiting for, not the
toolkit's real-time-tuned default, whenever the wait spans a virtualized sleep of more
than a second or so.

.. note::

    ``looptime`` virtualizes the event loop's own clock — ``asyncio.sleep``,
    ``loop.call_later``, ``loop.call_at`` — not only the calls a test's own engine makes. The
    real risk is not that a genuinely blocking call stays real-time and slips past it; it is
    that most async database drivers schedule their *own* deadlines the same way — Mongo's
    ``serverSelectionTimeoutMS`` and redis-py's ``socket_timeout`` both resolve through
    ``loop.call_later`` under the hood — so a virtual-time jump burns through them exactly as
    it burns through an engine's ``asyncio.sleep``. A 60-virtual-second jump can consume a
    driver's 30-second deadline in the middle of a real handshake that would otherwise finish
    in milliseconds (measured: 60 virtual seconds cost about 0.05s of real time), raising a
    timeout the driver would never have hit at a real clock's pace. It will not reproduce
    against a local database, where a round trip is sub-millisecond and a jump is unlikely to
    land inside one; against a slow or remote one it is a live hazard, so mark a test
    ``looptime`` only once its database calls are mocked, faked, or genuinely local.

Cleaning up background tasks
=============================

A bot with an engine of its own leaves tasks running past the end of a test —
``asyncio.create_task(self._night_timer())`` sleeping when the test itself already
returned. The loop is then torn down under them, and each one prints ``Task was destroyed
but it is pending!`` to stderr after the test that caused it has already passed, which is
noise nobody can trace back to its source. ``await bot_env.drain(timeout=...)`` cancels and
awaits every task the test left running, and reports how many there were:

.. code-block:: python

    async def test_night_phase_starts(bot_env, bot_user):
        await bot_user.send("/start")   # schedules a background timer

        await bot_env.drain()

Only tasks created *after* the environment was built count as this test's; a task already
running is left alone. "Already running" is checked twice, and the second check is the one
that matters in practice: the ``bot_env`` fixture is synchronous, so an environment is usually
built with no event loop running at all, and the snapshot taken at construction is empty. The
protection is extended again at this environment's **first asynchronous entry point** — the
first ``feed`` or the first intercepted Bot API call — which is the earliest moment a loop is
guaranteed to exist and still before the bot under test can have spawned anything of its own.
That is what spares a session-scoped fixture's own background worker: it is already running
by the time this environment does anything asynchronous, so it is protected exactly like a
task that predates construction, and the first test in a session to call ``drain()`` does not
kill it out from under every later test.

A task that fails on its own, or ends with something other than the cancellation ``drain()``
sent it, is not swallowed: retrieving its result is what stops asyncio complaining about it
later, and discarding that result would make ``drain()`` itself the thing hiding a real bug —
a night timer that died with a ``KeyError`` would look exactly like one cancelled on time. So
a failure is re-raised as :class:`aiogram.test.DrainedTaskError`, naming every task that
failed, with the first one's real traceback chained as its cause:

.. code-block:: python

    from aiogram.test import DrainedTaskError

    async def test_scheduler_reports_its_own_bug(bot_env, bot_user):
        await bot_user.send("/start")   # the scheduled task has a bug and will raise

        with pytest.raises(DrainedTaskError, match="ended with an exception"):
            await bot_env.drain()

A task that instead swallows its own cancellation and is still running after ``timeout``
raises :class:`~aiogram.test.WaitTimeoutError`, distinct from a task that ran and failed —
the two are different bugs and get different exceptions.

``drain`` is deliberately **not** called by ``dispose`` / ``dispose_sync``: the pytest
fixture's teardown is synchronous and cannot await anything, so an automatic drain would work
in one teardown path and silently not in the other — and cancelling tasks a test never
mentioned, as an invisible side effect of a fixture going out of scope, turns "my bot's
scheduler stopped" into a mystery. A test that wants its tasks gone says so.

.. warning::

    **A cache scoped above the test's own event loop is a different failure, and ``drain``
    does not touch it.** A package- or session-scoped ``bot_dispatcher`` fixture — the shape
    `Requirements and gotchas`_ already recommends, to dodge "Router is already attached" —
    keeps its middlewares alive across every test function, while each async test gets its
    *own* event loop by default. A middleware that opens a loop-bound resource the first
    time it runs — a Redis client inside a ``ThrottlingMiddleware``, most commonly — binds
    that resource to whichever loop happened to be running then, and every later test runs
    on a *different*, freshly created loop. This is the most expensive failure users of this
    toolkit hit, because it does not look like a caching bug: a handful of tests deep into a
    run start failing with an opaque error about a closed event loop or a socket used from
    the wrong one, and nothing about the failing tests themselves is wrong. Construct
    loop-bound resources **per test** instead — a function-scoped fixture building the Redis
    client and injecting it into the middleware, rather than the middleware opening one
    itself — or use a client that reconnects lazily per loop. ``drain`` cancels **tasks**; a
    stale cached connection is not a task, so no amount of draining reaches it.

Bots that use a global Bot instance
===================================

Many older codebases send through a module-level singleton — ``bot = get_bot()`` — rather
than the ``bot`` a handler receives through dependency injection. One fake session can
serve both:

.. code-block:: python

    bot = get_bot()
    bot.session = env.session
    bot._me = env.bot._me

Every Bot API call funnels through ``bot.session``, so pointing the global instance at the
environment's fake one routes its calls into the same world — messages it sends are
attributed to the blueprint's bot exactly as calls through ``bot_env.bot`` are, regardless
of what token the global instance itself was built with. Copying ``_me`` is the same
pre-seeding the environment already does for its own bot, so ``await bot.me()`` returns the
declared identity immediately rather than paying for a round trip the first time something
calls it. Calls made through the global instance land in the same call log as calls made
through the injected one, so ``env.calls`` and ``env.chat(...)`` see both.

What the global instance does *not* take over is the world's objects: a message it sends is
stored mounted to ``env.bot``, and a call of its own that returns that stored message hands
it back still mounted to ``env.bot``. Only objects minted for that call are mounted to the
global instance. Otherwise a single call through the singleton would re-point every later
shortcut on a stored message at the singleton's
:class:`~aiogram.client.default.DefaultBotProperties` — silently changing the ``parse_mode``
of messages sent much later in the test.

Joining and leaving
===================

Membership is driven by actors, and each trigger produces the update Telegram would:

.. code-block:: python

    await user.join()          # chat_member
    await user.leave()         # chat_member
    await user.add_bot()       # my_chat_member
    await user.remove_bot()    # my_chat_member

In a **group or supergroup**, ``join`` and ``add_bot`` also post the ``new_chat_members``
service message a real join or add delivers alongside the membership update — *after* it,
matching the order Telegram's own clients display the two in:

.. code-block:: python

    async def test_welcomes_new_members(env, dp, team, alice):
        welcomed = []

        @dp.message(F.new_chat_members)
        async def welcome(message):
            welcomed.append([user.id for user in message.new_chat_members])

        await alice.in_(team).add_bot()

        assert welcomed == [[env.world.bot_user.id]]

Pass ``service_message=False`` to get the old single-update behavior back. A **private**
chat never gets one — Telegram has no concept of "adding" someone to a DM — and ``leave`` /
``remove_bot`` are unaffected either way: only a join or an add ever produces it. The
trigger's own return value stays the membership update's handler result regardless; the
service message is fed but not awaited for its result, the same as any other update a
trigger feeds only for its side effects.

Promoting and demoting
-----------------------

``promote()``/``demote()`` are actor-level sugar over ``promoteChatMember``, spelled the
way the story usually goes — *someone* promotes *someone*:

.. code-block:: python

    await admin.in_(team).promote()                          # promotes the bot, no rights
    await admin.in_(team).promote(can_delete_messages=True)  # ...with one right
    await admin.in_(team).promote(subject=alice, can_pin_messages=True)  # promotes alice

    await admin.in_(team).demote()                # demotes the bot back to a plain member
    await admin.in_(team).demote(subject=alice)

``subject`` defaults to the bot itself — promoting the bot is the first thing almost every
group bot test needs — and otherwise accepts a declared user, a resolved state, or a bare
id. The rights passed are the *whole* mask, exactly like ``promoteChatMember`` itself: a
right ``promote()`` does not name is denied, not inherited from an earlier promotion.
Unlike a bare ``promoteChatMember(...)`` call, though, ``promote()`` with **no** rights at
all still promotes rather than reading as a demotion — there is no way to "explicitly grant
nothing" through this call, so nothing asked for is simply nothing granted; ``demote()`` is
what says "take the status away" instead. It drops the member to ``MEMBER`` and clears both
the granted rights and the custom title, while the member's ``tag`` survives it, since a
tag belongs to the membership rather than to the administrator status.

Dispatcher data goes through the keyword-only ``data=`` mapping, spelled the same way on
both triggers even though only ``promote()`` competes for the rest of its keyword space with
rights:

.. code-block:: python

    await admin.in_(team).promote(alice, can_pin_messages=True, data={"db": db})
    await admin.in_(team).demote(alice, data={"db": db})

A right ``promote()`` does not recognise is a typo, not something silently dropped — a
misspelled ``promote(can_pin_message=True)`` (missing the trailing ``s``) would otherwise
grant nothing and fail later on the bot's own "missing right" branch, with no clue which
right or why:

.. code-block:: python

    await admin.in_(team).promote(can_pin_message=True)
    # TypeError: ChatAdministratorRights has no right(s) can_pin_message, so promoting
    # with them would silently grant nothing.
    #   known rights: ...

Both refuse to touch the chat's owner, exactly as ``promoteChatMember`` does — raised as
:class:`~aiogram.test.WorldLookupError`, not the ``ApiRejection`` the raw call itself would
raise, since a trigger arranges the world rather than asking the API for anything:

.. code-block:: python

    await admin.in_(team).promote(subject=owner, can_delete_messages=True)
    # WorldLookupError: can't remove chat owner: this trigger arranges the world, and no
    # administrator can take the owner's standing away, so there is no state for it to
    # arrange. To test how the bot handles the API refusing its own promoteChatMember
    # call, have the bot make that call instead.

A join *request* is world state, so the approve and decline methods have something real to
act on:

.. code-block:: python

    @router.chat_join_request()
    async def vet(request: ChatJoinRequest, bot: Bot):
        await bot.approve_chat_join_request(request.chat.id, request.from_user.id)


    async def test_approves_known_users(env, group, user):
        await user.in_(group).request_join()

        assert group.member(user.user.id).is_present

Approving adds the requester as a member and clears the request; declining clears it
without adding them. Acting on a request that is not pending raises
:class:`aiogram.exceptions.TelegramBadRequest`, so a double approval fails the way it does
in production.

Chat administration
===================

Administering a chat mutates the world, so the already-modeled :code:`getChat` and
:code:`getChatMember` stop reporting stale values:

.. code-block:: python

    async def test_rename(env, group):
        await env.bot.set_chat_title(chat_id=group.id, title="Renamed")

        assert (await env.bot.get_chat(chat_id=group.id)).title == "Renamed"

Title, description, permissions and sticker set are stored and read back; deleting the chat
photo clears it. The membership reads are derived from the members the ban, unban, promote
and restrict methods already maintain, so :code:`getChatAdministrators` and
:code:`getChatMemberCount` cannot disagree with them. Administrators come back creator
first, and — as Telegram does — bots other than the one under test are omitted unless
``return_bots`` is passed.

Rights are stored, not invented. :code:`promoteChatMember` sets the whole rights mask on
every call, so that is what the world stores: a right the request does not pass is not
granted, and reading the member back says so.

.. code-block:: python

    await env.bot.promote_chat_member(chat_id=group.id, user_id=alice.id, can_pin_messages=True)

    member = await env.bot.get_chat_member(chat_id=group.id, user_id=alice.id)
    assert member.can_pin_messages is True
    assert member.can_delete_messages is False   # never granted

A promotion in which nothing comes out true — every flag ``False``, or none passed at all —
is the demotion the Bot API documents; anything true keeps the member an administrator,
``is_anonymous`` included. The chat's **owner** cannot be promoted, demoted, banned or
restricted: all four raise :class:`aiogram.exceptions.TelegramBadRequest` with Telegram's
own "can't remove chat owner", so a bot that moderates a list of users fails here rather
than only in production.

A demotion also drops the member's ``custom_title``, because a title is an *administrator's*:
:class:`~aiogram.types.chat_member_administrator.ChatMemberAdministrator` and
:class:`~aiogram.types.chat_member_owner.ChatMemberOwner` carry one and
:class:`~aiogram.types.chat_member_member.ChatMemberMember` has no field for it, so a title
outliving the status is nothing :code:`getChatMember` could report — it could only reappear,
ungranted, on some later promotion. ``tag`` is deliberately **not** dropped with it, and the
asymmetry is the Bot API's own: ``tag`` is a field of ``ChatMemberMember`` as much as of the
administrator variants, so it describes the membership rather than the administrator status,
and a demotion is not the API's way of taking one away.

What a member's rights *are* also depends on where they hold them, and so do the answers
here: ``can_post_messages`` and ``can_edit_messages`` are reported only in channels,
``can_manage_topics`` only in supergroups, ``can_pin_messages`` only in groups and
supergroups — everywhere else they come back ``None``, exactly as from the real API. A
right granted where it cannot exist is dropped rather than reported back as if it did.

Permissions are stored the way the Bot API grants them, which is not always the mask the
request passed. :code:`restrictChatMember` and :code:`setChatPermissions` both apply the
couplings they document: unless the call passes ``use_independent_chat_permissions=True``,
``can_send_other_messages`` and ``can_add_web_page_previews`` each grant every kind of
message, and ``can_send_polls`` grants ``can_send_messages``. So the permissions read back
may be **broader** than the ones handed in — as they would be against real Telegram, which
will not let a member send stickers while forbidding text:

.. code-block:: python

    await env.bot.restrict_chat_member(
        chat_id=group.id,
        user_id=alice.id,
        permissions=ChatPermissions(can_send_other_messages=True),
    )

    member = await env.bot.get_chat_member(chat_id=group.id, user_id=alice.id)
    assert member.can_send_messages is True    # implied, never passed
    assert member.can_send_photos is True      # implied, never passed

Passing ``use_independent_chat_permissions=True`` stores the mask exactly as given. It does
not switch off the three permissions that default to another one — ``can_react_to_messages``
follows ``can_send_messages``, ``can_edit_tag`` and ``can_manage_topics`` follow
``can_pin_messages`` — because the Bot API documents those on the
:class:`~aiogram.types.chat_permissions.ChatPermissions` fields themselves rather than on
either method. A bot that gates itself on ``can_send_messages`` therefore takes the same
branch here as it does in production.

Where Telegram posts a service message, so does the environment:

.. code-block:: python

    await env.bot.set_chat_title(chat_id=group.id, title="Renamed")

    assert group.messages[-1].new_chat_title == "Renamed"

That message counts in the chat's message list, so a test that renames a chat *and* counts
messages will see it.

Member annotations are not interchangeable, and the Bot API's own types say why:
:code:`setChatAdministratorCustomTitle` applies to an administrator, while
:code:`setChatMemberTag` applies to a regular member. Calling either on the wrong kind of
member raises rather than writing an annotation that would vanish on conversion.

.. warning::

    **Permissions are stored but never enforced.** Setting restrictive
    :class:`aiogram.types.chat_permissions.ChatPermissions`, or restricting a member, does
    not make a later ``sendMessage`` fail — the toolkit models the shape of administration,
    not its policy. A test that needs the rejection declares it:

    .. code-block:: python

        env.on(SendMessage).raises(TelegramBadRequest(method=..., message="Bad Request: ..."))

Invite links
============

Invite links are stored, so the pattern a real bot uses — create a link, keep its URL,
revoke it later — correlates instead of returning unrelated objects:

.. code-block:: python

    async def test_revokes_its_link(env, group):
        created = await env.bot.create_chat_invite_link(chat_id=group.id, name="Recruiting")

        revoked = await env.bot.revoke_chat_invite_link(
            chat_id=group.id,
            invite_link=created.invite_link,
        )

        assert revoked.invite_link == created.invite_link
        assert revoked.is_revoked

Editing and revoking return the *stored* link, mutated. A blueprint can declare links a
chat already has with :meth:`aiogram.test.Blueprint.add_invite_link`.

The two primary-link behaviors the Bot API documents are modeled:
:code:`exportChatInviteLink` revokes the previous primary link and returns a new one, and
revoking the primary link generates a replacement. :code:`getChat` reports the current
primary link, or ``None`` for a chat that never exported one.

The one validation is the one the Bot API states as a constant: a subscription period must
be 2592000 seconds. A :class:`datetime.timedelta` is accepted in its place, since aiogram
accepts one.

.. note::

    Links are **metadata only**. There is no join-by-link: ``member_limit`` gates nothing,
    ``expire_date`` never expires, and ``pending_join_request_count`` is not tracked.
    Membership is driven by actors — ``user.join()`` or ``user.request_join()`` — and a
    link's existence has no bearing on either.

    Correlate by the URL a call returned rather than by a literal; the format is an
    implementation detail.

Bot profile configuration
=========================

The bot's own configuration is world state, so the startup block almost every bot has can
be asserted on: commands, name, description, short description, default administrator
rights and menu buttons all round-trip.

.. code-block:: python

    async def test_startup_registers_commands(env):
        await on_startup(env.bot)

        assert await env.bot.get_my_commands() == [
            BotCommand(command="start", description="Start"),
        ]

A blueprint can declare a bot that is already configured, so a test that only *reads* the
profile needs no setup:

.. code-block:: python

    blueprint.set_bot_commands([BotCommand(command="start", description="Start")])
    blueprint.set_bot_profile(name="Helper", description="A helpful bot")

Two lookup rules apply, and they differ — because the Bot API's do:

* **Commands are exact.** :code:`getMyCommands` returns what was set for that precise
  scope *and* language, and an empty list otherwise. It does **not** fall back to a
  broader scope. The fallback the Bot API documents ("higher level commands will be shown
  to affected users") describes what users see in their client, not what the getter
  returns — modeling it would put the fake at odds with the real API.
* **The localized texts fall back by language.** A name, description or short description
  set with no ``language_code`` applies to every user without a dedicated one, so reading
  an unset language returns the default entry. Setting one to an empty string removes the
  dedicated entry and the fallback resumes. A menu button behaves the same way: a chat
  with no dedicated button reports the default one.

Reading something that was never set returns the value the Bot API documents — an empty
list, an empty string, :class:`aiogram.types.menu_button_default.MenuButtonDefault`,
all-``False`` administrator rights, and the bot's own first name for an unset bot name —
rather than a synthesized object. A bot that branches on "are my commands registered yet?"
therefore takes the same branch it would in production.

.. note::

    Nothing here is validated: command name syntax, text length limits and the scope
    constraints Telegram enforces are policy, not shape. A test that needs a rejection
    declares it with an override.

    The bot's profile *photo* (:code:`setMyProfilePhoto`, :code:`removeMyProfilePhoto`)
    stays record-only — it is media, and the Bot API offers no getter to read it back.

Polls and reactions
===================

A poll the bot sends is stored, so the assertion that motivated the whole toolkit — "the
poll the bot sent is now closed" — is writable:

.. code-block:: python

    async def test_poll_closes(env, chat, user):
        message = await env.bot.send_poll(
            chat_id=chat.id,
            question="Tabs or spaces?",
            options=["Tabs", "Spaces"],
            is_anonymous=False,
        )

        await user.vote(message.poll.id, [1])
        closed = await env.bot.stop_poll(chat_id=chat.id, message_id=message.message_id)

        assert closed.is_closed
        assert closed.options[1].voter_count == 1

Which update a poll delivers depends on its anonymity, and the environment models that
rather than letting a test drive one Telegram would never send: a **non-anonymous** poll
delivers ``poll_answer`` through ``user.vote(...)``, while an **anonymous** one delivers
the aggregate ``poll`` update through ``user.poll_update(...)``. Calling ``vote`` on an
anonymous poll raises and says so. Voting in a stopped poll raises too — Telegram simply
does not deliver such an answer, and a silent no-op would make a test pass while asserting
nothing.

Per-option counts are always computed from the recorded voters, so they cannot disagree
with who voted, including after a retraction (``user.vote(poll_id, [])``).

Reactions live in the chat rather than on the message, because **the Bot API has no
message field carrying them** — they exist only as update payloads:

.. code-block:: python

    await user.react(message, "👍")
    await user.react(message, "❤")     # replaces the first
    await user.react(message)           # removes it

    assert chat.reactions_for(message.message_id) == {user.user.id: [ReactionTypeEmoji(emoji="❤")]}
    assert chat.reaction_counts(message.message_id)[0].total_count == 1

``old_reaction`` is read before the change and ``new_reaction`` after, so a
``message_reaction`` handler sees the transition it would see in production.

The three reaction methods are *not* variations on one operation, despite their names:

.. list-table::
    :header-rows: 1

    * - Method
      - Scope
      - Whose reactions
    * - :code:`setMessageReaction`
      - one message
      - the bot's own
    * - :code:`deleteMessageReaction`
      - one message
      - a named user's (moderation)
    * - :code:`deleteAllMessageReactions`
      - the whole chat
      - a named user's (moderation)

:code:`deleteAllMessageReactions` takes no ``message_id`` at all — it removes one actor's
reactions across the chat, not every reaction on one message.

.. note::

    Quiz rules are not modeled: a vote for the wrong option is recorded, nothing is scored,
    no explanation is revealed and a second attempt is not blocked. Reaction permissions
    are not enforced, and paid reactions are not modeled. Anonymity decides which update
    kind is available, not whether the environment records who voted — a test needs
    distinct voters to drive.

Forum topics
============

Declare topics on a blueprint; the chat becomes a forum automatically:

.. code-block:: python

    @pytest.fixture
    def bot_blueprint():
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        team = blueprint.add_supergroup("Team")
        blueprint.add_topic(team, "Support")
        return blueprint

Bind an actor to a topic and every update it produces is threaded correctly — including
the bot's replies, which stay inside the topic exactly as they do in production:

.. code-block:: python

    async def test_support_topic(bot_env, bot_blueprint):
        alice, team = bot_blueprint.users[0], bot_blueprint.chats[0]
        support = bot_blueprint.topics[0]

        await bot_env.user(alice).in_(team, topic=support).send("/help")

        topic = bot_env.chat(team).topic(support.message_thread_id)
        assert topic.messages[-1].text == "How can we help?"

Topic state follows the real methods. Creating, editing, closing, reopening and deleting a
topic all mutate the world and emit the service message Telegram would post:

.. code-block:: python

    topic = await bot.create_forum_topic(chat_id=team.id, name="Bugs")
    assert chat.messages[-1].forum_topic_created.name == "Bugs"

    await bot.close_forum_topic(chat_id=team.id, message_thread_id=topic.message_thread_id)
    assert chat.topic(topic.message_thread_id).is_closed

The General topic is `chat.general_topic` — its messages carry no thread id, matching
Telegram — and the ``*GeneralForumTopic*`` methods act on it. Posting into a thread id that
does not exist raises :class:`aiogram.exceptions.TelegramBadRequest` rather than silently
producing an untagged message.

Business connections
====================

Declare the connections the bot acts on behalf of:

.. code-block:: python

    from aiogram.types import BusinessBotRights

    connection = blueprint.add_business_connection(
        owner,
        rights=BusinessBotRights(can_reply=True, can_read_messages=True),
    )

Binding an actor to a connection makes its triggers produce business updates:

.. code-block:: python

    actor = bot_env.user(customer).in_(chat, business=connection)

    await actor.send("is this available?")      # business_message
    await actor.edit(message, "corrected")      # edited_business_message
    await actor.disable_business_connection()   # business_connection
    await actor.delete_business_messages([7])   # deleted_business_messages

A message the bot sends on a connection is stored as sent by the **business account**,
with the bot recorded as the sending business bot — which is what the customer sees:

.. code-block:: python

    await bot.send_message(chat_id=chat.id, text="yes", business_connection_id=connection.id)

    stored = bot_env.chat(chat).messages[-1]
    assert stored.from_user.id == owner.id
    assert stored.sender_business_bot.id == bot_env.bot.id

``getBusinessConnection`` answers from the declared state, and ``readBusinessMessage`` and
``deleteBusinessMessages`` are applied to the world; the business *account* methods stay on
the record-and-synthesize path.

.. note::

    Rights are declared but **not enforced** — a bot that replies on a connection with
    ``can_reply=False`` succeeds here. The fake models shape, not policy.

Communities
===========

Communities have no Bot API methods, so the toolkit gives them a declaration and the two
service messages:

.. code-block:: python

    guild = blueprint.add_community("Guild", chats=[team])


    async def test_joins_a_community(bot_env, bot_blueprint):
        target = bot_blueprint.chats[1]
        actor = bot_env.user(alice).in_(target)

        await actor.add_chat_to_community(guild)

        full = await bot_env.bot.get_chat(chat_id=target.id)
        assert full.community.name == "Guild"

``remove_chat_from_community`` triggers the matching removal service message.

Requirements and gotchas
========================

**Async tests are your project's business.** The toolkit does not bundle or impose an
asyncio integration and does not set an event loop policy — configure ``pytest-asyncio``
or ``anyio`` as you normally would. With ``pytest-asyncio`` that means, at minimum:

.. code-block:: toml

    [tool.pytest.ini_options]
    asyncio_mode = "auto"

**A router can only be attached to one dispatcher, ever.** If your fixtures build a new
:class:`aiogram.dispatcher.dispatcher.Dispatcher` per test while your routers are
declared at module level, the second test fails with
``RuntimeError: Router is already attached``. Either keep the dispatcher fixture at a
wider scope — the environment isolates FSM state regardless — or detach the router
first:

.. code-block:: python

    from aiogram.test import detach_router


    @pytest.fixture
    def bot_dispatcher():
        dispatcher = Dispatcher()
        dispatcher.include_router(detach_router(router))
        return dispatcher

**Without the plugin.** Everything is importable, so projects that prefer their own
fixtures can build environments directly:

.. code-block:: python

    from aiogram.test import build_environment

    environment = build_environment(blueprint, dispatcher)
    try:
        ...
    finally:
        await environment.dispose()

Testing handlers directly
=========================

Handlers are regular async callables, so the simplest tests call them with a mocked
event object. Use this for business logic that lives inside a single handler and does not
need routing:

.. code-block:: python

    from unittest.mock import AsyncMock

    async def echo_handler(message):
        await message.answer(message.text)

    async def test_echo_handler():
        message = AsyncMock(text="Hello")

        await echo_handler(message)

        message.answer.assert_awaited_once_with("Hello")

You can also feed a raw update dictionary to a dispatcher yourself. This exercises the
routing pipeline without the toolkit, at the cost of hand-writing payloads:

.. code-block:: python

    import time

    from aiogram import Bot, Dispatcher, F

    async def test_dispatcher_routes_message():
        bot = Bot("42:TEST")
        dp = Dispatcher()

        @dp.message(F.text == "ping")
        async def ping_handler(message):
            return "pong"

        result = await dp.feed_raw_update(
            bot=bot,
            update={
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": int(time.time()),
                    "text": "ping",
                    "chat": {"id": 42, "type": "private"},
                    "from": {"id": 42, "is_bot": False, "first_name": "Test"},
                },
            },
        )

        assert result == "pong"

Avoid real bot tokens and real network requests in tests.

API reference
=============

.. automodule:: aiogram.test
    :members: Blueprint, BotTestEnvironment, UserActor, CallLog, RouteRecord, build_environment, default_blueprint, detach_router, administrator_rights
    :member-order: bysource
    :undoc-members: False

.. autoclass:: aiogram.test.world.ChatState
    :members: messages, members, pinned_message_ids, member, find_message, wait_for_message
    :member-order: bysource

.. autoclass:: aiogram.test.world.TopicState
    :members: messages, wait_for_message
    :member-order: bysource

.. autoclass:: aiogram.test.world.MemberState
    :members: status, rights, permissions, as_chat_member
    :member-order: bysource

.. autoclass:: aiogram.test.overrides.OverrideBuilder
    :members:
    :member-order: bysource

.. autoclass:: aiogram.test.OverrideHandle
    :members:
    :member-order: bysource

.. autoclass:: aiogram.test.MethodMatcher
    :members:
    :member-order: bysource

.. autoclass:: aiogram.test.WorldLookupError

.. autoclass:: aiogram.test.ApiRejection

.. autoclass:: aiogram.test.WaitTimeoutError

.. autoclass:: aiogram.test.DrainedTaskError

.. autoclass:: aiogram.test.NoFileContentError

Fixtures
--------

``bot_blueprint``
    The world declaration. Override at any scope to describe your own chats and users.

``bot_dispatcher``
    The dispatcher under test. Override it to include your real routers.

``bot_env``
    The isolated environment for one test — owns the bot, the world, the call log and
    the overrides.

``bot_chat``
    The first chat declared by the blueprint.

``bot_user``
    An actor for the first declared user, bound to the first declared chat.
