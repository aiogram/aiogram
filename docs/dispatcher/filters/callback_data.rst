.. _Callback data factory:

==============================
Callback Data Factory & Filter
==============================

.. autoclass:: aiogram.filters.callback_data.CallbackData
    :members:
    :member-order: bysource
    :undoc-members: False
    :exclude-members: model_config,model_fields

Usage
=====

Create subclass of :code:`CallbackData`:

.. code-block:: python

    class MyCallback(CallbackData, prefix="my"):
        foo: str
        bar: int

After that you can generate any callback based on this class, for example:

.. code-block:: python

    cb1 = MyCallback(foo="demo", bar=42)
    cb1.pack()  # returns 'my:demo:42'
    cb1.unpack('my:demo:42')  # returns <MyCallback(foo="demo", bar=42)>

So... Now you can use this class to generate any callbacks with defined structure

.. code-block:: python

    ...
    # Pass it into the markup
    InlineKeyboardButton(
        text="demo",
        callback_data=MyCallback(foo="demo", bar="42").pack()  # value should be packed to string
    )
    ...

... and handle by specific rules

.. code-block:: python

    # Filter callback by type and value of field :code:`foo`
    @router.callback_query(MyCallback.filter(F.foo == "demo"))
    async def my_callback_foo(query: CallbackQuery, callback_data: MyCallback):
        await query.answer(...)
        ...
        print("bar =", callback_data.bar)

Also can be used in :doc:`Keyboard builder </utils/keyboard>`:

.. code-block:: python

    builder = InlineKeyboardBuilder()
    builder.button(
        text="demo",
        callback_data=MyCallback(foo="demo", bar="42")  # Value can be not packed to string inplace, because builder knows what to do with callback instance
    )


Another abstract example:

.. code-block:: python

    class Action(str, Enum):
        ban = "ban"
        kick = "kick"
        warn = "warn"

    class AdminAction(CallbackData, prefix="adm"):
        action: Action
        chat_id: int
        user_id: int

    ...
    # Inside handler
    builder = InlineKeyboardBuilder()
    for action in Action:
        builder.button(
            text=action.value.title(),
            callback_data=AdminAction(action=action, chat_id=chat_id, user_id=user_id),
        )
    await bot.send_message(
        chat_id=admins_chat,
        text=f"What do you want to do with {html.quote(name)}",
        reply_markup=builder.as_markup(),
    )
    ...

    @router.callback_query(AdminAction.filter(F.action == Action.ban))
    async def ban_user(query: CallbackQuery, callback_data: AdminAction, bot: Bot):
        await bot.ban_chat_member(
            chat_id=callback_data.chat_id,
            user_id=callback_data.user_id,
            ...
        )

Known limitations
=================

Allowed types and their subclasses:

- :code:`str`
- :code:`int`
- :code:`bool`
- :code:`float`
- :code:`Decimal`  (:code:`from decimal import Decimal`)
- :code:`Fraction`  (:code:`from fractions import Fraction`)
- :code:`UUID` (:code:`from uuid import UUID`)
- :code:`Enum` (:code:`from enum import Enum`, only for string enums)
- :code:`IntEnum` (:code:`from enum import IntEnum`, only for int enums)


.. note::

    Note that the integer Enum's should be always is subclasses of :code:`IntEnum` in due to parsing issues.
