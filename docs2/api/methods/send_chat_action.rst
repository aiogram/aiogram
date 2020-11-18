##############
sendChatAction
##############

Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns True on success.

Example: The ImageBot needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use sendChatAction with action = upload_photo. The user will see a 'sending photo' status for the bot.

We only recommend using this method when a response from the bot will take a noticeable amount of time to arrive.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.send_chat_action
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.send_chat_action(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendChatAction`
- :code:`from aiogram.methods import SendChatAction`
- :code:`from aiogram.methods.send_chat_action import SendChatAction`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SendChatAction(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SendChatAction(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendChatAction(...)