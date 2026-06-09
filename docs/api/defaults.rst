===============
Global defaults
===============

aiogram provides mechanism to set some global defaults for all requests to Telegram Bot API
in your application using :class:`aiogram.client.default.DefaultBotProperties` class.

There are some properties that can be set:

.. autoclass:: aiogram.client.default.DefaultBotProperties
    :members:
    :member-order: bysource
    :undoc-members: True

.. note::

    If you need to override default properties for some requests, you should use `aiogram.client.default.DefaultBotProperties`
    only for properties that you want to set as defaults and pass explicit values for other properties.

.. danger::

    If you upgrading from aiogram 3.0-3.6 to 3.7,
    you should update your code to use `aiogram.client.default.DefaultBotProperties`.

Example
=======

Here is an example of setting default parse mode for all requests to Telegram Bot API:

.. code-block:: python

    bot = Bot(
        token=...,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        )
    )

In this case all messages sent by this bot will be parsed as HTML, so you don't need to specify `parse_mode`
in every message you send.

Instead of

.. code-block:: python

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)

you can use

.. code-block:: python

    await bot.send_message(chat_id, text)

and the message will be sent with HTML parse mode.

In some cases you may want to override default properties for some requests. You can do it by passing
explicit values to the method:

.. code-block:: python

    await bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)

In this case the message will be sent with Markdown parse mode instead of default HTML.

Another example of overriding default properties:

.. code-block:: python

    await bot.send_message(chat_id, text, parse_mode=None)

In this case the message will be send withoout parse mode, even if default parse mode is set it may be useful
if you want to send message with plain text or :ref:`aiogram.types.message_entity.MessageEntity`.

.. code-block:: python

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        entities=[MessageEntity(type='bold', offset=0, length=4)],
        parse_mode=None
    )
