
..
    Copy-pasted and reformatted from GitHub releases page


2.14.3 (2021-07-21)
===================

- Fixed :code:`ChatMember` type detection via adding customizable object serialization mechanism (`#624 <https://github.com/aiogram/aiogram/issues/624>`_, `#623 <https://github.com/aiogram/aiogram/issues/623>`_)


2.14.2 (2021-07-26)
===================

- Fixed :code:`MemoryStorage` cleaner (`#619 <https://github.com/aiogram/aiogram/issues/619>`_)
- Fixed unused default locale in :code:`I18nMiddleware` (`#562 <https://github.com/aiogram/aiogram/issues/562>`_, `#563 <https://github.com/aiogram/aiogram/issues/563>`_)


2.14 (2021-07-27)
=================

- Full support of Bot API 5.3 (`#610 <https://github.com/aiogram/aiogram/issues/610>`_, `#614 <https://github.com/aiogram/aiogram/issues/614>`_)
- Fixed :code:`Message.send_copy` method for polls (`#603 <https://github.com/aiogram/aiogram/issues/603>`_)
- Updated pattern for :code:`GroupDeactivated` exception (`#549 <https://github.com/aiogram/aiogram/issues/549>`_
- Added :code:`caption_entities` field in :code:`InputMedia` base class (`#583 <https://github.com/aiogram/aiogram/issues/583>`_)
- Fixed HTML text decorations for tag :code:`pre` (`#597 <https://github.com/aiogram/aiogram/issues/597>`_ fixes issues `#596 <https://github.com/aiogram/aiogram/issues/596>`_ and `#481 <https://github.com/aiogram/aiogram/issues/481>`_)
- Fixed :code:`Message.get_full_command` method for messages with caption (`#576 <https://github.com/aiogram/aiogram/issues/576>`_)
- Improved :code:`MongoStorage`: remove documents with empty data from :code:`aiogram_data` collection to save memory. (`#609 <https://github.com/aiogram/aiogram/issues/609>`_)


2.13 (2021-04-28)
=================

- Added full support of Bot API 5.2 (`#572 <https://github.com/aiogram/aiogram/issues/572>`_)
- Fixed usage of :code:`provider_data` argument in :code:`sendInvoice` method call
- Fixed builtin command filter args (`#556 <https://github.com/aiogram/aiogram/issues/556>`_) (`#558 <https://github.com/aiogram/aiogram/issues/558>`_)
- Allowed to use State instances FSM storage directly (`#542 <https://github.com/aiogram/aiogram/issues/542>`_)
- Added possibility to get i18n locale without User instance (`#546 <https://github.com/aiogram/aiogram/issues/546>`_)
- Fixed returning type of :code:`Bot.*_chat_invite_link()` methods `#548 <https://github.com/aiogram/aiogram/issues/548>`_ (`#549 <https://github.com/aiogram/aiogram/issues/549>`_)
- Fixed deep-linking util (`#569 <https://github.com/aiogram/aiogram/issues/569>`_)
- Small changes in documentation - describe limits in docstrings corresponding to the current limit. (`#565 <https://github.com/aiogram/aiogram/issues/565>`_)
- Fixed internal call to deprecated 'is_private' method (`#553 <https://github.com/aiogram/aiogram/issues/553>`_)
- Added possibility to use :code:`allowed_updates` argument in Polling mode (`#564 <https://github.com/aiogram/aiogram/issues/564>`_)


2.12.1 (2021-03-22)
===================

- Fixed :code:`TypeError: Value should be instance of 'User' not 'NoneType'` (`#527 <https://github.com/aiogram/aiogram/issues/527>`_)
- Added missing :code:`Chat.message_auto_delete_time` field (`#535 <https://github.com/aiogram/aiogram/issues/535>`_)
- Added :code:`MediaGroup` filter (`#528 <https://github.com/aiogram/aiogram/issues/528>`_)
- Added :code:`Chat.delete_message` shortcut (`#526 <https://github.com/aiogram/aiogram/issues/526>`_)
- Added mime types parsing for :code:`aiogram.types.Document` (`#431 <https://github.com/aiogram/aiogram/issues/431>`_)
- Added warning in :code:`TelegramObject.__setitem__` when Telegram adds a new field (`#532 <https://github.com/aiogram/aiogram/issues/532>`_)
- Fixed :code:`examples/chat_type_filter.py` (`#533 <https://github.com/aiogram/aiogram/issues/533>`_)
- Removed redundant definitions in framework code (`#531 <https://github.com/aiogram/aiogram/issues/531>`_)


2.12 (2021-03-14)
=================

- Full support for Telegram Bot API 5.1 (`#519 <https://github.com/aiogram/aiogram/issues/519>`_)
- Fixed sending playlist of audio files and documents (`#465 <https://github.com/aiogram/aiogram/issues/465>`_, `#468 <https://github.com/aiogram/aiogram/issues/468>`_)
- Fixed :code:`FSMContextProxy.setdefault` method (`#491 <https://github.com/aiogram/aiogram/issues/491>`_)
- Fixed :code:`Message.answer_location` and :code:`Message.reply_location` unable to send live location (`#497 <https://github.com/aiogram/aiogram/issues/497>`_)
- Fixed :code:`user_id` and :code:`chat_id` getters from the context at Dispatcher :code:`check_key`, :code:`release_key` and :code:`throttle` methods (`#520 <https://github.com/aiogram/aiogram/issues/520>`_)
- Fixed :code:`Chat.update_chat` method and all similar situations (`#516 <https://github.com/aiogram/aiogram/issues/516>`_)
- Fixed :code:`MediaGroup` attach methods (`#514 <https://github.com/aiogram/aiogram/issues/514>`_)
- Fixed state filter for inline keyboard query callback in groups (`#508 <https://github.com/aiogram/aiogram/issues/508>`_, `#510 <https://github.com/aiogram/aiogram/issues/510>`_)
- Added missing :code:`ContentTypes.DICE` (`#466 <https://github.com/aiogram/aiogram/issues/466>`_)
- Added missing vcard argument to :code:`InputContactMessageContent` constructor (`#473 <https://github.com/aiogram/aiogram/issues/473>`_)
- Add missing exceptions: :code:`MessageIdInvalid`, :code:`CantRestrictChatOwner` and :code:`UserIsAnAdministratorOfTheChat` (`#474 <https://github.com/aiogram/aiogram/issues/474>`_, `#512 <https://github.com/aiogram/aiogram/issues/512>`_)
- Added :code:`answer_chat_action` to the :code:`Message` object (`#501 <https://github.com/aiogram/aiogram/issues/501>`_)
- Added dice to :code:`message.send_copy` method (`#511 <https://github.com/aiogram/aiogram/issues/511>`_)
- Removed deprecation warning from :code:`Message.send_copy`
- Added an example of integration between externally created aiohttp Application and aiogram (`#433 <https://github.com/aiogram/aiogram/issues/433>`_)
- Added :code:`split_separator` argument to :code:`safe_split_text` (`#515 <https://github.com/aiogram/aiogram/issues/515>`_)
- Fixed some typos in docs and examples (`#489 <https://github.com/aiogram/aiogram/issues/489>`_, `#490 <https://github.com/aiogram/aiogram/issues/490>`_, `#498 <https://github.com/aiogram/aiogram/issues/498>`_, `#504 <https://github.com/aiogram/aiogram/issues/504>`_, `#514 <https://github.com/aiogram/aiogram/issues/514>`_)


2.11.2 (2021-11-10)
===================

- Fixed default parse mode
- Added missing "supports_streaming" argument to answer_video method `#462 <https://github.com/aiogram/aiogram/issues/462>`_


2.11.1 (2021-11-10)
===================

- Fixed files URL template
- Fix MessageEntity serialization for API calls `#457 <https://github.com/aiogram/aiogram/issues/457>`_
- When entities are set, default parse_mode become disabled (`#461 <https://github.com/aiogram/aiogram/issues/461>`_)
- Added parameter supports_streaming to reply_video, remove redundant docstrings (`#459 <https://github.com/aiogram/aiogram/issues/459>`_)
- Added missing parameter to promoteChatMember alias (`#458 <https://github.com/aiogram/aiogram/issues/458>`_)


2.11 (2021-11-08)
=================

- Added full support of Telegram Bot API 5.0 (`#454 <https://github.com/aiogram/aiogram/issues/454>`_)
- Added possibility to more easy specify custom API Server (example)
    - WARNING: API method :code:`close` was named in Bot class as close_bot in due to Bot instance already has method with the same name. It will be changed in :code:`aiogram 3.0`
- Added alias to Message object :code:`Message.copy_to` with deprecation of :code:`Message.send_copy`
- :code:`ChatType.SUPER_GROUP` renamed to :code:`ChatType.SUPERGROUP` (`#438 <https://github.com/aiogram/aiogram/issues/438>`_)


2.10.1 (2021-09-14)
===================

- Fixed critical bug with getting asyncio event loop in executor. (`#424 <https://github.com/aiogram/aiogram/issues/424>`_) :code:`AttributeError: 'NoneType' object has no attribute 'run_until_complete'`


2.10 (2021-09-13)
==================

- Breaking change: Stop using _MainThread event loop in bot/dispatcher instances (`#397 <https://github.com/aiogram/aiogram/issues/397>`_)
- Breaking change: Replaced aiomongo with motor (`#368 <https://github.com/aiogram/aiogram/issues/368>`_, `#380 <https://github.com/aiogram/aiogram/issues/380>`_)
- Fixed: TelegramObject's aren't destroyed after update handling `#307 <https://github.com/aiogram/aiogram/issues/307>`_ (`#371 <https://github.com/aiogram/aiogram/issues/371>`_)
- Add setting current context of Telegram types (`#369 <https://github.com/aiogram/aiogram/issues/369>`_)
- Fixed markdown escaping issues (`#363 <https://github.com/aiogram/aiogram/issues/363>`_)
- Fixed HTML characters escaping (`#409 <https://github.com/aiogram/aiogram/issues/409>`_)
- Fixed italic and underline decorations when parse entities to Markdown
- Fixed `#413 <https://github.com/aiogram/aiogram/issues/413>`_: parse entities positioning (`#414 <https://github.com/aiogram/aiogram/issues/414>`_)
- Added missing thumb parameter (`#362 <https://github.com/aiogram/aiogram/issues/362>`_)
- Added public methods to register filters and middlewares (`#370 <https://github.com/aiogram/aiogram/issues/370>`_)
- Added ChatType builtin filter (`#356 <https://github.com/aiogram/aiogram/issues/356>`_)
- Fixed IDFilter checking message from channel (`#376 <https://github.com/aiogram/aiogram/issues/376>`_)
- Added missed answer_poll and reply_poll (`#384 <https://github.com/aiogram/aiogram/issues/384>`_)
- Added possibility to ignore message caption in commands filter (`#383 <https://github.com/aiogram/aiogram/issues/383>`_)
- Fixed addStickerToSet method
- Added preparing thumb in send_document method (`#391 <https://github.com/aiogram/aiogram/issues/391>`_)
- Added exception MessageToPinNotFound (`#404 <https://github.com/aiogram/aiogram/issues/404>`_)
- Fixed handlers parameter-spec solving (`#408 <https://github.com/aiogram/aiogram/issues/408>`_)
- Fixed CallbackQuery.answer() returns nothing (`#420 <https://github.com/aiogram/aiogram/issues/420>`_)
- CHOSEN_INLINE_RESULT is a correct API-term (`#415 <https://github.com/aiogram/aiogram/issues/415>`_)
- Fixed missing attributes for Animation class (`#422 <https://github.com/aiogram/aiogram/issues/422>`_)
- Added missed emoji argument to reply_dice (`#395 <https://github.com/aiogram/aiogram/issues/395>`_)
- Added is_chat_creator method to ChatMemberStatus (`#394 <https://github.com/aiogram/aiogram/issues/394>`_)
- Added missed ChatPermissions to __all__ (`#393 <https://github.com/aiogram/aiogram/issues/393>`_)
- Added is_forward method to Message (`#390 <https://github.com/aiogram/aiogram/issues/390>`_)
- Fixed usage of deprecated is_private function (`#421 <https://github.com/aiogram/aiogram/issues/421>`_)

and many others documentation and examples changes:

- Updated docstring of RedisStorage2 (`#423 <https://github.com/aiogram/aiogram/issues/423>`_)
- Updated I18n example (added docs and fixed typos) (`#419 <https://github.com/aiogram/aiogram/issues/419>`_)
- A little documentation revision (`#381 <https://github.com/aiogram/aiogram/issues/381>`_)
- Added comments about correct errors_handlers usage (`#398 <https://github.com/aiogram/aiogram/issues/398>`_)
- Fixed typo rexex -> regex (`#386 <https://github.com/aiogram/aiogram/issues/386>`_)
- Fixed docs Quick start page code blocks (`#417 <https://github.com/aiogram/aiogram/issues/417>`_)
- fixed type hints of callback_data (`#400 <https://github.com/aiogram/aiogram/issues/400>`_)
- Prettify readme, update downloads stats badge (`#406 <https://github.com/aiogram/aiogram/issues/406>`_)


2.9.2 (2021-06-13)
==================

- Fixed :code:`Message.get_full_command()` `#352 <https://github.com/aiogram/aiogram/issues/352>`_
- Fixed markdown util `#353 <https://github.com/aiogram/aiogram/issues/353>`_


2.9 (2021-06-08)
================

- Added full support of Telegram Bot API 4.9
- Fixed user context at poll_answer update (`#322 <https://github.com/aiogram/aiogram/issues/322>`_)
- Fix Chat.set_description (`#325 <https://github.com/aiogram/aiogram/issues/325>`_)
- Add lazy session generator (`#326 <https://github.com/aiogram/aiogram/issues/326>`_)
- Fix text decorations (`#315 <https://github.com/aiogram/aiogram/issues/315>`_, `#316 <https://github.com/aiogram/aiogram/issues/316>`_, `#328 <https://github.com/aiogram/aiogram/issues/328>`_)
- Fix missing :code:`InlineQueryResultPhoto` :code:`parse_mode` field (`#331 <https://github.com/aiogram/aiogram/issues/331>`_)
- Fix fields from parent object in :code:`KeyboardButton` (`#344 <https://github.com/aiogram/aiogram/issues/344>`_ fixes `#343 <https://github.com/aiogram/aiogram/issues/343>`_)
- Add possibility to get bot id without calling :code:`get_me` (`#296 <https://github.com/aiogram/aiogram/issues/296>`_)


2.8 (2021-04-26)
================

- Added full support of Bot API 4.8
- Added :code:`Message.answer_dice` and :code:`Message.reply_dice` methods (`#306 <https://github.com/aiogram/aiogram/issues/306>`_)


2.7 (2021-04-07)
================

- Added full support of Bot API 4.7 (`#294 <https://github.com/aiogram/aiogram/issues/294>`_ `#289 <https://github.com/aiogram/aiogram/issues/289>`_)
- Added default parse mode for send_animation method (`#293 <https://github.com/aiogram/aiogram/issues/293>`_ `#292 <https://github.com/aiogram/aiogram/issues/292>`_)
- Added new API exception when poll requested in public chats (`#270 <https://github.com/aiogram/aiogram/issues/270>`_)
- Make correct User and Chat get_mention methods (`#277 <https://github.com/aiogram/aiogram/issues/277>`_)
- Small changes and other minor improvements


2.6.1 (2021-01-25)
==================

- Fixed reply :code:`KeyboardButton` initializer with :code:`request_poll` argument (`#266 <https://github.com/aiogram/aiogram/issues/266>`_)
- Added helper for poll types (:code:`aiogram.types.PollType`)
- Changed behavior of Telegram_object :code:`.as_*` and :code:`.to_*` methods. It will no more mutate the object. (`#247 <https://github.com/aiogram/aiogram/issues/247>`_)


2.6 (2021-01-23)
================

- Full support of Telegram Bot API v4.6 (Polls 2.0) `#265 <https://github.com/aiogram/aiogram/issues/265>`_
- Aded new filter - IsContactSender (commit)
- Fixed proxy extra dependencies version `#262 <https://github.com/aiogram/aiogram/issues/262>`_


2.5.3 (2021-01-05)
==================

- `#255 <https://github.com/aiogram/aiogram/issues/255>`_ Updated CallbackData factory validity check. More correct for non-latin symbols
- `#256 <https://github.com/aiogram/aiogram/issues/256>`_ Fixed :code:`renamed_argument` decorator error
- `#257 <https://github.com/aiogram/aiogram/issues/257>`_ One more fix of CommandStart filter


2.5.2 (2021-01-01)
==================

- Get back :code:`quote_html` and :code:`escape_md` functions


2.5.1 (2021-01-01)
==================

- Hot-fix of :code:`CommandStart` filter


2.5 (2021-01-01)
================

- Added full support of Telegram Bot API 4.5 (`#250 <https://github.com/aiogram/aiogram/issues/250>`_, `#251 <https://github.com/aiogram/aiogram/issues/251>`_)
- `#239 <https://github.com/aiogram/aiogram/issues/239>`_ Fixed :code:`check_token` method
- `#238 <https://github.com/aiogram/aiogram/issues/238>`_, `#241 <https://github.com/aiogram/aiogram/issues/241>`_: Added deep-linking utils
- `#248 <https://github.com/aiogram/aiogram/issues/248>`_ Fixed support of aiohttp-socks
- Updated setup.py. No more use of internal pip API
- Updated links to documentations (https://docs.aiogram.dev)
- Other small changes and minor improvements (`#223 <https://github.com/aiogram/aiogram/issues/223>`_ and others...)


2.4 (2021-10-29)
================

- Added Message.send_copy method (forward message without forwarding)
- Safe close of aiohttp client session (no more exception when application is shutdown)
- No more "adWanced" words in project `#209 <https://github.com/aiogram/aiogram/issues/209>`_
- Arguments user and chat is renamed to user_id and chat_id in Dispatcher.throttle method `#196 <https://github.com/aiogram/aiogram/issues/196>`_
- Fixed set_chat_permissions `#198 <https://github.com/aiogram/aiogram/issues/198>`_
- Fixed Dispatcher polling task does not process cancellation `#199 <https://github.com/aiogram/aiogram/issues/199>`_, `#201 <https://github.com/aiogram/aiogram/issues/201>`_
- Fixed compatibility with latest asyncio version `#200 <https://github.com/aiogram/aiogram/issues/200>`_
- Disabled caching by default for lazy_gettext method of I18nMiddleware `#203 <https://github.com/aiogram/aiogram/issues/203>`_
- Fixed HTML user mention parser `#205 <https://github.com/aiogram/aiogram/issues/205>`_
- Added IsReplyFilter `#210 <https://github.com/aiogram/aiogram/issues/210>`_
- Fixed send_poll method arguments `#211 <https://github.com/aiogram/aiogram/issues/211>`_
- Added OrderedHelper `#215 <https://github.com/aiogram/aiogram/issues/215>`_
- Fix incorrect completion order. `#217 <https://github.com/aiogram/aiogram/issues/217>`_


2.3 (2021-08-16)
================

- Full support of Telegram Bot API 4.4
- Fixed `#143 <https://github.com/aiogram/aiogram/issues/143>`_
- Added new filters from issue `#151 <https://github.com/aiogram/aiogram/issues/151>`_: `#172 <https://github.com/aiogram/aiogram/issues/172>`_, `#176 <https://github.com/aiogram/aiogram/issues/176>`_, `#182 <https://github.com/aiogram/aiogram/issues/182>`_
- Added expire argument to RedisStorage2 and other storage fixes `#145 <https://github.com/aiogram/aiogram/issues/145>`_
- Fixed JSON and Pickle storages `#138 <https://github.com/aiogram/aiogram/issues/138>`_
- Implemented MongoStorage `#153 <https://github.com/aiogram/aiogram/issues/153>`_ based on aiomongo (soon motor will be also added)
- Improved tests
- Updated examples
- Warning: Updated auth widget util. `#190 <https://github.com/aiogram/aiogram/issues/190>`_
- Implemented throttle decorator `#181 <https://github.com/aiogram/aiogram/issues/181>`_


2.2 (2021-06-09)
================

- Provides latest Telegram Bot API (4.3)
- Updated docs for filters
- Added opportunity to use different bot tokens from single bot instance (via context manager, `#100 <https://github.com/aiogram/aiogram/issues/100>`_)
- IMPORTANT: Fixed Typo: :code:`data` -> :code:`bucket` in :code:`update_bucket` for RedisStorage2 (`#132 <https://github.com/aiogram/aiogram/issues/132>`_)


2.1 (2021-04-18)
================

- Implemented all new features from Telegram Bot API 4.2
- :code:`is_member` and :code:`is_admin` methods of :code:`ChatMember` and :code:`ChatMemberStatus` was renamed to :code:`is_chat_member` and :code:`is_chat_admin`
- Remover func filter
- Added some useful Message edit functions (:code:`Message.edit_caption`, :code:`Message.edit_media`, :code:`Message.edit_reply_markup`) (`#121 <https://github.com/aiogram/aiogram/issues/121>`_, `#103 <https://github.com/aiogram/aiogram/issues/103>`_, `#104 <https://github.com/aiogram/aiogram/issues/104>`_, `#112 <https://github.com/aiogram/aiogram/issues/112>`_)
- Added requests timeout for all methods (`#110 <https://github.com/aiogram/aiogram/issues/110>`_)
- Added :code:`answer*` methods to :code:`Message` object (`#112 <https://github.com/aiogram/aiogram/issues/112>`_)
- Maked some improvements of :code:`CallbackData` factory
- Added deep-linking parameter filter to :code:`CommandStart` filter
- Implemented opportunity to use DNS over socks (`#97 <https://github.com/aiogram/aiogram/issues/97>`_ -> `#98 <https://github.com/aiogram/aiogram/issues/98>`_)
- Implemented logging filter for extending LogRecord attributes (Will be usefull with external logs collector utils like GrayLog, Kibana and etc.)
- Updated :code:`requirements.txt` and :code:`dev_requirements.txt` files
- Other small changes and minor improvements


2.0.1 (2021-12-31)
==================

- Implemented CallbackData factory (`example <https://github.com/aiogram/aiogram/blob/master/examples/callback_data_factory.py>`_)
- Implemented methods for answering to inline query from context and reply with animation to the messages. `#85 <https://github.com/aiogram/aiogram/issues/85>`_
- Fixed installation from tar.gz `#84 <https://github.com/aiogram/aiogram/issues/84>`_
- More exceptions (:code:`ChatIdIsEmpty` and :code:`NotEnoughRightsToRestrict`)


2.0 (2021-10-28)
================

This update will break backward compability with Python 3.6 and works only with Python 3.7+:
- contextvars (PEP-567);
- New syntax for annotations (PEP-563).

Changes:
- Used contextvars instead of :code:`aiogram.utils.context`;
- Implemented filters factory;
- Implemented new filters mechanism;
- Allowed to customize command prefix in CommandsFilter;
- Implemented mechanism of passing results from filters (as dicts) as kwargs in handlers (like fixtures in pytest);
- Implemented states group feature;
- Implemented FSM storage's proxy;
- Changed files uploading mechanism;
- Implemented pipe for uploading files from URL;
- Implemented I18n Middleware;
- Errors handlers now should accept only two arguments (current update and exception);
- Used :code:`aiohttp_socks` instead of :code:`aiosocksy` for Socks4/5 proxy;
- types.ContentType was divided to :code:`types.ContentType` and :code:`types.ContentTypes`;
- Allowed to use rapidjson instead of ujson/json;
- :code:`.current()` method in bot and dispatcher objects was renamed to :code:`get_current()`;

Full changelog
- You can read more details about this release in migration FAQ: `<https://aiogram.readthedocs.io/en/latest/migration_1_to_2.html>`_


1.4 (2021-08-03)
================

- Bot API 4.0 (`#57 <https://github.com/aiogram/aiogram/issues/57>`_)


1.3.3 (2021-07-16)
==================

- Fixed markup-entities parsing;
- Added more API exceptions;
- Now InlineQueryResultLocation has live_period;
- Added more message content types;
- Other small changes and minor improvements.


1.3.2 (2021-05-27)
==================

- Fixed crashing of polling process. (i think)
- Added parse_mode field into input query results according to Bot API Docs.
- Added new methods for Chat object. (`#42 <https://github.com/aiogram/aiogram/issues/42>`_, `#43 <https://github.com/aiogram/aiogram/issues/43>`_)
- **Warning**: disabled connections limit for bot aiohttp session.
- **Warning**: Destroyed "temp sessions" mechanism.
- Added new error types.
- Refactored detection of error type.
- Small fixes of executor util.
- Fixed RethinkDBStorage

1.3.1 (2018-05-27)
==================


1.3 (2021-04-22)
================

- Allow to use Socks5 proxy (need manually install :code:`aiosocksy`).
- Refactored :code:`aiogram.utils.executor` module.
- **[Warning]** Updated requirements list.


1.2.3 (2018-04-14)
==================

- Fixed API errors detection
- Fixed compability of :code:`setup.py` with pip 10.0.0


1.2.2 (2018-04-08)
==================

- Added more error types.
- Implemented method :code:`InputFile.from_url(url: str)` for downloading files.
- Implemented big part of API method tests.
- Other small changes and mminor improvements.


1.2.1 (2018-03-25)
==================

- Fixed handling Venue's [`#27 <https://github.com/aiogram/aiogram/issues/27>`_, `#26 <https://github.com/aiogram/aiogram/issues/26>`_]
- Added parse_mode to all medias (Bot API 3.6 support) [`#23 <https://github.com/aiogram/aiogram/issues/23>`_]
- Now regexp filter can be used with callback query data [`#19 <https://github.com/aiogram/aiogram/issues/19>`_]
- Improvements in :code:`InlineKeyboardMarkup` & :code:`ReplyKeyboardMarkup` objects [`#21 <https://github.com/aiogram/aiogram/issues/21>`_]
- Other bug & typo fixes and minor improvements.


1.2 (2018-02-23)
================

- Full provide Telegram Bot API 3.6
- Fixed critical error: :code:`Fatal Python error: PyImport_GetModuleDict: no module dictionary!`
- Implemented connection pool in RethinkDB driver
- Typo fixes of documentstion
- Other bug fixes and minor improvements.


1.1 (2018-01-27)
================

- Added more methods for data types (like :code:`message.reply_sticker(...)` or :code:`file.download(...)`
- Typo fixes of documentstion
- Allow to set default parse mode for messages (:code:`Bot( ... , parse_mode='HTML')`)
- Allowed to cancel event from the :code:`Middleware.on_pre_process_<event type>`
- Fixed sending files with correct names.
- Fixed MediaGroup
- Added RethinkDB storage for FSM (:code:`aiogram.contrib.fsm_storage.rethinkdb`)


1.0.4 (2018-01-10)
==================


1.0.3 (2018-01-07)
==================

- Added middlewares mechanism.
- Added example for middlewares and throttling manager.
- Added logging middleware (:code:`aiogram.contrib.middlewares.logging.LoggingMiddleware`)
- Fixed handling errors in async tasks (marked as 'async_task')
- Small fixes and other minor improvements.


1.0.2 (2017-11-29)
==================


1.0.1 (2017-11-21)
==================

- Implemented :code:`types.InputFile` for more easy sending local files
- **Danger!** Fixed typo in word pooling. Now whatever all methods with that word marked as deprecated and original methods is renamed to polling. Check it in you'r code before updating!
- Fixed helper for chat actions (:code:`types.ChatActions`)
- Added `example <https://github.com/aiogram/aiogram/blob/master/examples/media_group.py>`_ for media group.


1.0 (2017-11-19)
================

- Remaked data types serialozation/deserialization mechanism (Speed up).
- Fully rewrited all Telegram data types.
- Bot object was fully rewritted (regenerated).
- Full provide Telegram Bot API 3.4+ (with sendMediaGroup)
- Warning: Now :code:`BaseStorage.close()` is awaitable! (FSM)
- Fixed compability with uvloop.
- More employments for :code:`aiogram.utils.context`.
- Allowed to disable :code:`ujson`.
- Other bug fixes and minor improvements.
- Migrated from Bitbucket to Github.


0.4.1 (2017-08-03)
==================


0.4 (2017-08-05)
================


0.3.4 (2017-08-04)
==================


0.3.3 (2017-07-05)
==================


0.3.2 (2017-07-04)
==================


0.3.1 (2017-07-04)
==================


0.2b1 (2017-06-00)
==================


0.1 (2017-06-03)
================
