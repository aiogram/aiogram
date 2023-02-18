=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "CHANGES".

    WARNING: Don't drop the next directive!

.. towncrier-draft-entries:: |release| [UNRELEASED DRAFT]

.. towncrier release notes start

3.0.0b7 (2023-02-18)
=====================

Features
--------

- Added missing shortcuts, new enums, reworked old stuff

  **Breaking**
  All previously added enums is re-generated in new place - `aiogram.enums` instead of `aiogram.types`

  **Added enums:** :class:`aiogram.enums.bot_command_scope_type.BotCommandScopeType`,
      :class:`aiogram.enums.chat_action.ChatAction`,
      :class:`aiogram.enums.chat_member_status.ChatMemberStatus`,
      :class:`aiogram.enums.chat_type.ChatType`,
      :class:`aiogram.enums.content_type.ContentType`,
      :class:`aiogram.enums.dice_emoji.DiceEmoji`,
      :class:`aiogram.enums.inline_query_result_type.InlineQueryResultType`,
      :class:`aiogram.enums.input_media_type.InputMediaType`,
      :class:`aiogram.enums.mask_position_point.MaskPositionPoint`,
      :class:`aiogram.enums.menu_button_type.MenuButtonType`,
      :class:`aiogram.enums.message_entity_type.MessageEntityType`,
      :class:`aiogram.enums.parse_mode.ParseMode`,
      :class:`aiogram.enums.poll_type.PollType`,
      :class:`aiogram.enums.sticker_type.StickerType`,
      :class:`aiogram.enums.topic_icon_color.TopicIconColor`,
      :class:`aiogram.enums.update_type.UpdateType`,

  **Added shortcuts**:

  - *Chat* :meth:`aiogram.types.chat.Chat.get_administrators`,
      :meth:`aiogram.types.chat.Chat.delete_message`,
      :meth:`aiogram.types.chat.Chat.revoke_invite_link`,
      :meth:`aiogram.types.chat.Chat.edit_invite_link`,
      :meth:`aiogram.types.chat.Chat.create_invite_link`,
      :meth:`aiogram.types.chat.Chat.export_invite_link`,
      :meth:`aiogram.types.chat.Chat.do`,
      :meth:`aiogram.types.chat.Chat.delete_sticker_set`,
      :meth:`aiogram.types.chat.Chat.set_sticker_set`,
      :meth:`aiogram.types.chat.Chat.get_member`,
      :meth:`aiogram.types.chat.Chat.get_member_count`,
      :meth:`aiogram.types.chat.Chat.leave`,
      :meth:`aiogram.types.chat.Chat.unpin_all_messages`,
      :meth:`aiogram.types.chat.Chat.unpin_message`,
      :meth:`aiogram.types.chat.Chat.pin_message`,
      :meth:`aiogram.types.chat.Chat.set_administrator_custom_title`,
      :meth:`aiogram.types.chat.Chat.set_permissions`,
      :meth:`aiogram.types.chat.Chat.promote`,
      :meth:`aiogram.types.chat.Chat.restrict`,
      :meth:`aiogram.types.chat.Chat.unban`,
      :meth:`aiogram.types.chat.Chat.ban`,
      :meth:`aiogram.types.chat.Chat.set_description`,
      :meth:`aiogram.types.chat.Chat.set_title`,
      :meth:`aiogram.types.chat.Chat.delete_photo`,
      :meth:`aiogram.types.chat.Chat.set_photo`,
  - *Sticker*: :meth:`aiogram.types.sticker.Sticker.set_position_in_set`,
      :meth:`aiogram.types.sticker.Sticker.delete_from_set`,
  - *User*: :meth:`aiogram.types.user.User.get_profile_photos`
  `#952 <https://github.com/aiogram/aiogram/issues/952>`_
- Added :ref:`callback answer <callback-answer-util>` feature
  `#1091 <https://github.com/aiogram/aiogram/issues/1091>`_
- Added a method that allows you to compactly register routers
  `#1117 <https://github.com/aiogram/aiogram/issues/1117>`_


Bugfixes
--------

- Check status code when downloading file
  `#816 <https://github.com/aiogram/aiogram/issues/816>`_
- Fixed `ignore_case` parameter in :obj:`aiogram.filters.command.Command` filter
  `#1106 <https://github.com/aiogram/aiogram/issues/1106>`_


Misc
----

- Added integration with new code-generator named `Butcher <https://github.com/aiogram/butcher>`_
  `#1069 <https://github.com/aiogram/aiogram/issues/1069>`_
- Added full support of `Bot API 6.4 <https://core.telegram.org/bots/api-changelog#december-30-2022>`_
  `#1088 <https://github.com/aiogram/aiogram/issues/1088>`_
- Updated package metadata, moved build internals from Poetry to Hatch, added contributing guides.
  `#1095 <https://github.com/aiogram/aiogram/issues/1095>`_
- Added full support of `Bot API 6.5 <https://core.telegram.org/bots/api-changelog#february-3-2023>`_

  .. danger::

      Note that :obj:`aiogram.types.chat_permissions.ChatPermissions` is updated without
      backward compatibility, so now this object has no :code:`can_send_media_messages` attribute
  `#1112 <https://github.com/aiogram/aiogram/issues/1112>`_
- Replaced error :code:`TypeError: TelegramEventObserver.__call__() got an unexpected keyword argument '<name>'`
  with a more understandable one for developers and with a link to the documentation.
  `#1114 <https://github.com/aiogram/aiogram/issues/1114>`_
- Added possibility to reply into webhook with files
  `#1120 <https://github.com/aiogram/aiogram/issues/1120>`_
- Reworked graceful shutdown. Added method to stop polling.
  Now polling started from dispatcher can be stopped by signals gracefully without errors (on Linux and Mac).
  `#1124 <https://github.com/aiogram/aiogram/issues/1124>`_


3.0.0b6 (2022-11-18)
=====================

Features
--------

- (again) Added possibility to combine filters with an *and*/*or* operations.

  Read more in ":ref:`Combining filters <combining-filters>`" documentation section
  `#1018 <https://github.com/aiogram/aiogram/issues/1018>`_
- Added following methods to ``Message`` class:

  - :code:`Message.forward(...)`
  - :code:`Message.edit_media(...)`
  - :code:`Message.edit_live_location(...)`
  - :code:`Message.stop_live_location(...)`
  - :code:`Message.pin(...)`
  - :code:`Message.unpin()`
  `#1030 <https://github.com/aiogram/aiogram/issues/1030>`_
- Added following methods to :code:`User` class:

  - :code:`User.mention_markdown(...)`
  - :code:`User.mention_html(...)`
  `#1049 <https://github.com/aiogram/aiogram/issues/1049>`_
- Added full support of `Bot API 6.3 <https://core.telegram.org/bots/api-changelog#november-5-2022>`_
  `#1057 <https://github.com/aiogram/aiogram/issues/1057>`_


Bugfixes
--------

- Fixed :code:`Message.send_invoice` and :code:`Message.reply_invoice`, added missing arguments
  `#1047 <https://github.com/aiogram/aiogram/issues/1047>`_
- Fixed copy and forward in:

  - :code:`Message.answer(...)`
  - :code:`Message.copy_to(...)`
  `#1064 <https://github.com/aiogram/aiogram/issues/1064>`_


Improved Documentation
----------------------

- Fixed UA translations in index.po
  `#1017 <https://github.com/aiogram/aiogram/issues/1017>`_
- Fix typehints for :code:`Message`, :code:`reply_media_group` and :code:`answer_media_group` methods
  `#1029 <https://github.com/aiogram/aiogram/issues/1029>`_
- Removed an old now non-working feature
  `#1060 <https://github.com/aiogram/aiogram/issues/1060>`_


Misc
----

- Enabled testing on Python 3.11
  `#1044 <https://github.com/aiogram/aiogram/issues/1044>`_
- Added a mandatory dependency :code:`certifi` in due to in some cases on systems that doesn't have updated ca-certificates the requests to Bot API fails with reason :code:`[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain`
  `#1066 <https://github.com/aiogram/aiogram/issues/1066>`_


3.0.0b5 (2022-10-02)
=====================

Features
--------

- Add PyPy support and run tests under PyPy
  `#985 <https://github.com/aiogram/aiogram/issues/985>`_
- Added message text to aiogram exceptions representation
  `#988 <https://github.com/aiogram/aiogram/issues/988>`_
- Added warning about using magic filter from `magic_filter` instead of `aiogram`'s ones.
  Is recommended to use `from aiogram import F` instead of `from magic_filter import F`
  `#990 <https://github.com/aiogram/aiogram/issues/990>`_
- Added more detailed error when server response can't be deserialized. This feature will help to debug unexpected responses from the Server
  `#1014 <https://github.com/aiogram/aiogram/issues/1014>`_


Bugfixes
--------

- Reworked error event, introduced :class:`aiogram.types.error_event.ErrorEvent` object.
  `#898 <https://github.com/aiogram/aiogram/issues/898>`_
- Fixed escaping markdown in `aiogram.utils.markdown` module
  `#903 <https://github.com/aiogram/aiogram/issues/903>`_
- Fixed polling crash when Telegram Bot API raises HTTP 429 status-code.
  `#995 <https://github.com/aiogram/aiogram/issues/995>`_
- Fixed empty mention in command parsing, now it will be None instead of an empty string
  `#1013 <https://github.com/aiogram/aiogram/issues/1013>`_


Improved Documentation
----------------------

- Initialized Docs translation (added Ukrainian language)
  `#925 <https://github.com/aiogram/aiogram/issues/925>`_


Deprecations and Removals
-------------------------

- Removed filters factory as described in corresponding issue.
  `#942 <https://github.com/aiogram/aiogram/issues/942>`_


Misc
----

- Now Router/Dispatcher accepts only keyword arguments.
  `#982 <https://github.com/aiogram/aiogram/issues/982>`_


3.0.0b4 (2022-08-14)
=====================

Features
--------

- Add class helper ChatAction for constants that Telegram BotAPI uses in sendChatAction request.
  In my opinion, this will help users and will also improve compatibility with 2.x version
  where similar class was called "ChatActions".
  `#803 <https://github.com/aiogram/aiogram/issues/803>`_
- Added possibility to combine filters or invert result

  Example:

  .. code-block:: python

      Text(text="demo") | Command(commands=["demo"])
      MyFilter() & AnotherFilter()
      ~StateFilter(state='my-state')

  `#894 <https://github.com/aiogram/aiogram/issues/894>`_
- Fixed type hints for redis TTL params.
  `#922 <https://github.com/aiogram/aiogram/issues/922>`_
- Added `full_name` shortcut for `Chat` object
  `#929 <https://github.com/aiogram/aiogram/issues/929>`_


Bugfixes
--------

- Fixed false-positive coercing of Union types in API methods
  `#901 <https://github.com/aiogram/aiogram/issues/901>`_
- Added 3 missing content types:

  * proximity_alert_triggered
  * supergroup_chat_created
  * channel_chat_created
  `#906 <https://github.com/aiogram/aiogram/issues/906>`_
- Fixed the ability to compare the state, now comparison to copy of the state will return `True`.
  `#927 <https://github.com/aiogram/aiogram/issues/927>`_
- Fixed default lock kwargs in RedisEventIsolation.
  `#972 <https://github.com/aiogram/aiogram/issues/972>`_


Misc
----

- Restrict including routers with strings
  `#896 <https://github.com/aiogram/aiogram/issues/896>`_
- Changed CommandPatterType to CommandPatternType in `aiogram/dispatcher/filters/command.py`
  `#907 <https://github.com/aiogram/aiogram/issues/907>`_
- Added full support of `Bot API 6.1 <https://core.telegram.org/bots/api-changelog#june-20-2022>`_
  `#936 <https://github.com/aiogram/aiogram/issues/936>`_
- **Breaking!** More flat project structure

  These packages was moved, imports in your code should be fixed:

  - :code:`aiogram.dispatcher.filters` -> :code:`aiogram.filters`
  - :code:`aiogram.dispatcher.fsm` -> :code:`aiogram.fsm`
  - :code:`aiogram.dispatcher.handler` -> :code:`aiogram.handler`
  - :code:`aiogram.dispatcher.webhook` -> :code:`aiogram.webhook`
  - :code:`aiogram.dispatcher.flags/*` -> :code:`aiogram.dispatcher.flags` (single module instead of package)
  `#938 <https://github.com/aiogram/aiogram/issues/938>`_
- Removed deprecated :code:`router.<event>_handler` and :code:`router.register_<event>_handler` methods.
  `#941 <https://github.com/aiogram/aiogram/issues/941>`_
- Deprecated filters factory. It will be removed in next Beta (3.0b5)
  `#942 <https://github.com/aiogram/aiogram/issues/942>`_
- `MessageEntity` method `get_text` was removed and `extract` was renamed to `extract_from`
  `#944 <https://github.com/aiogram/aiogram/issues/944>`_
- Added full support of `Bot API 6.2 <https://core.telegram.org/bots/api-changelog#august-12-2022>`_
  `#975 <https://github.com/aiogram/aiogram/issues/975>`_


3.0.0b3 (2022-04-19)
=====================

Features
--------

- Added possibility to get command magic result as handler argument
  `#889 <https://github.com/aiogram/aiogram/issues/889>`_
- Added full support of `Telegram Bot API 6.0 <https://core.telegram.org/bots/api-changelog#april-16-2022>`_
  `#890 <https://github.com/aiogram/aiogram/issues/890>`_


Bugfixes
--------

- Fixed I18n lazy-proxy. Disabled caching.
  `#839 <https://github.com/aiogram/aiogram/issues/839>`_
- Added parsing of spoiler message entity
  `#865 <https://github.com/aiogram/aiogram/issues/865>`_
- Fixed default `parse_mode` for `Message.copy_to()` method.
  `#876 <https://github.com/aiogram/aiogram/issues/876>`_
- Fixed CallbackData factory parsing IntEnum's
  `#885 <https://github.com/aiogram/aiogram/issues/885>`_


Misc
----

- Added automated check that pull-request adds a changes description to **CHANGES** directory
  `#873 <https://github.com/aiogram/aiogram/issues/873>`_
- Changed :code:`Message.html_text` and :code:`Message.md_text` attributes behaviour when message has no text.
  The empty string will be used instead of raising error.
  `#874 <https://github.com/aiogram/aiogram/issues/874>`_
- Used `redis-py` instead of `aioredis` package in due to this packages was merged into single one
  `#882 <https://github.com/aiogram/aiogram/issues/882>`_
- Solved common naming problem with middlewares that confusing too much developers
  - now you can't see the `middleware` and `middlewares` attributes at the same point
  because this functionality encapsulated to special interface.
  `#883 <https://github.com/aiogram/aiogram/issues/883>`_


3.0.0b2 (2022-02-19)
=====================

Features
--------

- Added possibility to pass additional arguments into the aiohttp webhook handler to use this
  arguments inside handlers as the same as it possible in polling mode.
  `#785 <https://github.com/aiogram/aiogram/issues/785>`_
- Added possibility to add handler flags via decorator (like `pytest.mark` decorator but `aiogram.flags`)
  `#836 <https://github.com/aiogram/aiogram/issues/836>`_
- Added :code:`ChatActionSender` utility to automatically sends chat action while long process is running.

  It also can be used as message middleware and can be customized via :code:`chat_action` flag.
  `#837 <https://github.com/aiogram/aiogram/issues/837>`_


Bugfixes
--------

- Fixed unexpected behavior of sequences in the StateFilter.
  `#791 <https://github.com/aiogram/aiogram/issues/791>`_
- Fixed exceptions filters
  `#827 <https://github.com/aiogram/aiogram/issues/827>`_


Misc
----

- Logger name for processing events is changed to :code:`aiogram.events`.
  `#830 <https://github.com/aiogram/aiogram/issues/830>`_
- Added full support of Telegram Bot API 5.6 and 5.7
  `#835 <https://github.com/aiogram/aiogram/issues/835>`_
- **BREAKING**
  Events isolation mechanism is moved from FSM storages to standalone managers
  `#838 <https://github.com/aiogram/aiogram/issues/838>`_


3.0.0b1 (2021-12-12)
=====================

Features
--------

- Added new custom operation for MagicFilter named :code:`as_`

  Now you can use it to get magic filter result as handler argument

  .. code-block:: python

      from aiogram import F

      ...

      @router.message(F.text.regexp(r"^(\d+)$").as_("digits"))
      async def any_digits_handler(message: Message, digits: Match[str]):
          await message.answer(html.quote(str(digits)))


      @router.message(F.photo[-1].as_("photo"))
      async def download_photos_handler(message: Message, photo: PhotoSize, bot: Bot):
          content = await bot.download(photo)
  `#759 <https://github.com/aiogram/aiogram/issues/759>`_


Bugfixes
--------

- Fixed: Missing :code:`ChatMemberHandler` import in :code:`aiogram/dispatcher/handler`
  `#751 <https://github.com/aiogram/aiogram/issues/751>`_


Misc
----

- Check :code:`destiny` in case of no :code:`with_destiny` enabled in RedisStorage key builder
  `#776 <https://github.com/aiogram/aiogram/issues/776>`_
- Added full support of `Bot API 5.5 <https://core.telegram.org/bots/api-changelog#december-7-2021>`_
  `#777 <https://github.com/aiogram/aiogram/issues/777>`_
- Stop using feature from #336. From now settings of client-session should be placed as initializer arguments instead of changing instance attributes.
  `#778 <https://github.com/aiogram/aiogram/issues/778>`_
- Make TelegramAPIServer files wrapper in local mode bi-directional (server-client, client-server)
  Now you can convert local path to server path and server path to local path.
  `#779 <https://github.com/aiogram/aiogram/issues/779>`_


3.0.0a18 (2021-11-10)
======================

Features
--------

- Breaking: Changed the signature of the session middlewares
  Breaking: Renamed AiohttpSession.make_request method parameter from call to method to match the naming in the base class
  Added middleware for logging outgoing requests
  `#716 <https://github.com/aiogram/aiogram/issues/716>`_
- Improved description of filters resolving error.
  For example when you try to pass wrong type of argument to the filter but don't know why filter is not resolved now you can get error like this:

  .. code-block:: python3

      aiogram.exceptions.FiltersResolveError: Unknown keyword filters: {'content_types'}
        Possible cases:
        - 1 validation error for ContentTypesFilter
          content_types
            Invalid content types {'42'} is not allowed here (type=value_error)
  `#717 <https://github.com/aiogram/aiogram/issues/717>`_
- **Breaking internal API change**
  Reworked FSM Storage record keys propagation
  `#723 <https://github.com/aiogram/aiogram/issues/723>`_
- Implemented new filter named :code:`MagicData(magic_data)` that helps to filter event by data from middlewares or other filters

  For example your bot is running with argument named :code:`config` that contains the application config then you can filter event by value from this config:

  .. code-block:: python3

      @router.message(magic_data=F.event.from_user.id == F.config.admin_id)
      ...
  `#724 <https://github.com/aiogram/aiogram/issues/724>`_


Bugfixes
--------

- Fixed I18n context inside error handlers
  `#726 <https://github.com/aiogram/aiogram/issues/726>`_
- Fixed bot session closing before emit shutdown
  `#734 <https://github.com/aiogram/aiogram/issues/734>`_
- Fixed: bound filter resolving does not require children routers
  `#736 <https://github.com/aiogram/aiogram/issues/736>`_


Misc
----

- Enabled testing on Python 3.10
  Removed `async_lru` dependency (is incompatible with Python 3.10) and replaced usage with protected property
  `#719 <https://github.com/aiogram/aiogram/issues/719>`_
- Converted README.md to README.rst and use it as base file for docs
  `#725 <https://github.com/aiogram/aiogram/issues/725>`_
- Rework filters resolving:

  - Automatically apply Bound Filters with default values to handlers
  - Fix data transfer from parent to included routers filters
  `#727 <https://github.com/aiogram/aiogram/issues/727>`_
- Added full support of Bot API 5.4
  https://core.telegram.org/bots/api-changelog#november-5-2021
  `#744 <https://github.com/aiogram/aiogram/issues/744>`_


3.0.0a17 (2021-09-24)
======================

Misc
----

- Added :code:`html_text` and :code:`md_text` to Message object
  `#708 <https://github.com/aiogram/aiogram/issues/708>`_
- Refactored I18n, added context managers for I18n engine and current locale
  `#709 <https://github.com/aiogram/aiogram/issues/709>`_


3.0.0a16 (2021-09-22)
======================

Features
--------

- Added support of local Bot API server files downloading

  When Local API is enabled files can be downloaded via `bot.download`/`bot.download_file` methods.
  `#698 <https://github.com/aiogram/aiogram/issues/698>`_
- Implemented I18n & L10n support
  `#701 <https://github.com/aiogram/aiogram/issues/701>`_


Misc
----

- Covered by tests and docs KeyboardBuilder util
  `#699 <https://github.com/aiogram/aiogram/issues/699>`_
- **Breaking!!!**. Refactored and renamed exceptions.

  - Exceptions module was moved from :code:`aiogram.utils.exceptions` to :code:`aiogram.exceptions`
  - Added prefix `Telegram` for all error classes
  `#700 <https://github.com/aiogram/aiogram/issues/700>`_
- Replaced all :code:`pragma: no cover` marks via global :code:`.coveragerc` config
  `#702 <https://github.com/aiogram/aiogram/issues/702>`_
- Updated dependencies.

  **Breaking for framework developers**
  Now all optional dependencies should be installed as extra: `poetry install -E fast -E redis -E proxy -E i18n -E docs`
  `#703 <https://github.com/aiogram/aiogram/issues/703>`_


3.0.0a15 (2021-09-10)
======================

Features
--------

- Ability to iterate over all states in StatesGroup.
  Aiogram already had in check for states group so this is relative feature.
  `#666 <https://github.com/aiogram/aiogram/issues/666>`_


Bugfixes
--------

- Fixed incorrect type checking in the :class:`aiogram.utils.keyboard.KeyboardBuilder`
  `#674 <https://github.com/aiogram/aiogram/issues/674>`_


Misc
----

- Disable ContentType filter by default
  `#668 <https://github.com/aiogram/aiogram/issues/668>`_
- Moved update type detection from Dispatcher to Update object
  `#669 <https://github.com/aiogram/aiogram/issues/669>`_
- Updated **pre-commit** config
  `#681 <https://github.com/aiogram/aiogram/issues/681>`_
- Reworked **handlers_in_use** util. Function moved to Router as method **.resolve_used_update_types()**
  `#682 <https://github.com/aiogram/aiogram/issues/682>`_


3.0.0a14 (2021-08-17)
======================

Features
--------

- add aliases for edit/delete reply markup to Message
  `#662 <https://github.com/aiogram/aiogram/issues/662>`_
- Reworked outer middleware chain. Prevent to call many times the outer middleware for each nested router
  `#664 <https://github.com/aiogram/aiogram/issues/664>`_


Bugfixes
--------

- Prepare parse mode for InputMessageContent in AnswerInlineQuery method
  `#660 <https://github.com/aiogram/aiogram/issues/660>`_


Improved Documentation
----------------------

- Added integration with :code:`towncrier`
  `#602 <https://github.com/aiogram/aiogram/issues/602>`_


Misc
----

- Added `.editorconfig`
  `#650 <https://github.com/aiogram/aiogram/issues/650>`_
- Redis storage speedup globals
  `#651 <https://github.com/aiogram/aiogram/issues/651>`_
- add allow_sending_without_reply param to Message reply aliases
  `#663 <https://github.com/aiogram/aiogram/issues/663>`_
