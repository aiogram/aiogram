==========================
Migration FAQ (1.4 -> 2.0)
==========================

This update make breaking changes in aiogram API and drop backward capability with previous versions of framework.

From this point aiogram supports only Python 3.7 and newer.

Changelog
=========

- Used contextvars instead of `aiogram.utils.context`;
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
- Used `aiohttp_socks` instead of `aiosocksy` for Socks4/5 proxy;
- `types.ContentType` was divided to `types.ContentType` and `types.ContentTypes`;
- Allowed to use rapidjson instead of ujson/json;
- `.current()` method in bot and dispatcher objects was renamed to `get_current()`;

Instructions
============

Contextvars
-----------
Context utility (`aiogram.utils.context`) now is removed due to new features of Python 3.7 and all subclasses of :obj:`aiogram.types.base.TelegramObject`, :obj:`aiogram.Bot` and :obj:`aiogram.Dispatcher` has `.get_current()` and `.set_current()` methods for getting/setting contextual instances of objects.

Example:

.. code-block:: python

    async def my_handler(message: types.Message):
        bot = Bot.get_current()
        user = types.User.get_current()
        ...

Filters
-------

Custom filters
~~~~~~~~~~~~~~

Now `func` keyword argument can't be used for passing filters to the list of filters instead of that you can pass the filters as arguments:

.. code-block:: python

    @dp.message_handler(lambda message: message.text == 'foo')
    @dp.message_handler(types.ChatType.is_private, my_filter)
    async def ...

(func filter is still available until v2.1)

Filters factory
~~~~~~~~~~~~~~~
Also you can bind your own filters for using as keyword arguments:

.. code-block:: python

    from aiogram.dispatcher.filters import BoundFilter

    class MyFilter(BoundFilter):
        key = 'is_admin'
        
        def __init__(self, is_admin):
            self.is_admin = is_admin
            
        async def check(self, message: types.Message):
            member = await bot.get_chat_member(message.chat.id, message.from_user.id)
            return member.is_chat_admin()

    dp.filters_factory.bind(MyFilter)

    @dp.message_handler(is_admin=True)
    async def ...


Customize commands prefix
~~~~~~~~~~~~~~~~~~~~~~~~~

Commands prefix can be changed by following one of two available methods:

.. code-block:: python

    @dp.message_handler(commands=['admin'], commands_prefix='!/')
    @dp.message_handler(Command('admin', prefixes='!/'))
    async def ...

Passing data from filters as keyword arguments to the handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can pass any data from any filter to the handler by returning :obj:`dict`
If any key from the received dictionary not in the handler specification the key will be skipped and and will be unavailable from the handler

Before (<=v1.4)

.. code-block:: python

    async def my_filter(message: types.Message):
        # do something here
        message.conf['foo'] = 'foo'
        message.conf['bar'] = 42
        return True

    @dp.message_handler(func=my_filter)
    async def my_message_handler(message: types.Message):
        bar = message.conf["bar"]
        await message.reply(f'bar = {bar}')


Now (v2.0)

.. code-block:: python

    async def my_filter(message: types.Message):
        # do something here
        return {'foo': 'foo', 'bar': 42}

    @dp.message_handler(my_filter)
    async def my_message_handler(message: types.Message, bar: int):
        await message.reply(f'bar = {bar}')


Other
~~~~~
Filters can also be used as logical expressions:

.. code-block:: python

    Text(equals='foo') | Text(endswith='Bar') | ~Text(contains='spam')


States group
------------

You can use States objects and States groups instead of string names of the states.
String values is still also be available.

Writing states group:

.. code-block:: python

    from aiogram.dispatcher.filters.state import State, StatesGroup

    class UserForm(StatesGroup):
        name = State()  # Will be represented in storage as 'Form:name'
        age = State()  # Will be represented in storage as 'Form:age'
        gender = State()  # Will be represented in storage as 'Form:gender'

After that you can use states as `UserForm.name` and etc.

FSM storage's proxy
-------------------
Now `Dispatcher.current_context()` can't be used as context-manager.

Implemented `FSMContext.proxy()` method which returns asynchronous `FSMContextProxy` context manager and can be used for more simply getting data from the storage.

`FSMContextProxy`  load all user-related data on initialization and dump it to the storage when proxy is closing if any part of the data was changed.


Usage:

.. code-block:: python

    @dp.message_handler(commands=['click'])
    async def cmd_start(message: types.Message, state: FSMContext):
        async with state.proxy() as proxy:  # proxy = FSMContextProxy(state); await proxy.load()
            proxy.setdefault('counter', 0)
            proxy['counter'] += 1
            return await message.reply(f"Counter: {proxy['counter']}")


This method is not recommended in high-load solutions in reason named "race-condition".


File uploading mechanism
------------------------
Fixed uploading files. Removed `BaseBot.send_file` method. This allowed to send the `thumb` field.

Pipe for uploading files from URL
---------------------------------
Known issue when Telegram can not accept sending file as URL. In this case need to download file locally and then send.

In this case now you can send file from URL by using pipe. That means you download and send the file without saving it.

You can open the pipe and use for uploading by calling `types.InputFile.from_file(<URL>)`

Example:

.. code-block:: python

    URL = 'https://docs.aiogram.dev/en/dev-2.x/_static/logo.png'


    @dp.message_handler(commands=['image, img'])
    async def cmd_image(message: types.Message):
        await bot.send_photo(message.chat.id, types.InputFile.from_url(URL))

I18n Middleware
---------------
You can internalize your bot by following next steps:

(Code snippets in this example related with `examples/i18n_example.py`)

First usage
~~~~~~~~~~~
1. Extract texts

    .. code-block:: bash

        pybabel extract i18n_example.py -o locales/mybot.pot

2. Create `*.po` files. For e.g. create `en`, `ru`, `uk` locales.
3. Translate texts
4. Compile translations

    .. code-block:: bash

        pybabel compile -d locales -D mybot

Updating translations
~~~~~~~~~~~~~~~~~~~~~
When you change the code of your bot you need to update `po` & `mo` files:

1. Regenerate pot file:

    .. code-block:: bash

        pybabel extract i18n_example.py -o locales/mybot.pot

2. Update po files

    .. code-block:: bash

        pybabel update -d locales -D mybot -i locales/mybot.pot

3. Update your translations
4. Compile `mo` files

    .. code-block:: bash

        pybabel compile -d locales -D mybot

Error handlers
--------------
Previously errors handlers had to have three arguments `dispatcher`, `update` and `exception` now `dispatcher` argument is removed and will no longer be passed to the error handlers.


Content types
-------------

Content types helper was divided to `types.ContentType` and `types.ContentTypes`.

In filters you can use `types.ContentTypes` but for comparing content types you must use `types.ContentType` class.
