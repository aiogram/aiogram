###########
sendSticker
###########

Use this method to send static .WEBP or animated .TGS stickers. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_sticker
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_sticker(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendSticker`
- :code:`from aiogram.api.methods import SendSticker`
- :code:`from aiogram.api.methods.send_sticker import SendSticker`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendSticker(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendSticker(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendSticker(...)