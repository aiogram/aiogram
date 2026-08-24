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

The handles returned by ``add_user`` / ``add_private_chat`` / ``add_group`` are how you
address participants later:

.. code-block:: python

    async def test_group_flow(bot_env, bot_blueprint):
        alice, bob = bot_blueprint.users
        team = bot_blueprint.chats[1]

        await bot_env.user(alice).in_(team).send("/report")

        assert bot_env.chat(team).messages[-1].text.startswith("Report")

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

Results carry the bot
=====================

A real session parses every response with the bot in the validation context, which is what
lets you call a shortcut on whatever a method returned. The fake does the same to the
objects it hands back, so results — and everything nested inside them, including the items
of a list result — are usable, not just readable:

.. code-block:: python

    message = await bot_env.bot.send_message(chat_id=bot_chat.id, text="hi")
    await message.edit_text("bye")

    reply = await message.reply("re")
    await reply.reply_to_message.delete()  # nested objects are mounted too

    for admin in await bot_env.bot.get_chat_administrators(chat_id=bot_chat.id):
        await admin.user.get_profile_photos()  # so are the items of a list result

One consequence is shared with production: the bot an object is mounted to is part of its
identity for pydantic, so a returned object never compares equal to an identical one built
inside the test. Compare the payload instead:

.. code-block:: python

    assert message.reply_markup.model_dump() == markup.model_dump()

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

Joining and leaving
===================

Membership is driven by actors, and each trigger produces the update Telegram would:

.. code-block:: python

    await user.join()          # chat_member
    await user.leave()         # chat_member
    await user.add_bot()       # my_chat_member
    await user.remove_bot()    # my_chat_member

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
    :members: Blueprint, BotTestEnvironment, UserActor, CallLog, build_environment, default_blueprint, detach_router
    :member-order: bysource
    :undoc-members: False

.. autoclass:: aiogram.test.world.ChatState
    :members: messages, members, pinned_message_ids, member, find_message
    :member-order: bysource

.. autoclass:: aiogram.test.overrides.OverrideBuilder
    :members:
    :member-order: bysource

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
