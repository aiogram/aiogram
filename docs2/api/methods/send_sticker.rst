###########
sendSticker
###########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_sticker
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.send_sticker import SendSticker`
- alias: :code:`from aiogram.methods import SendSticker`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Message = await SendSticker(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendSticker(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendSticker(...)