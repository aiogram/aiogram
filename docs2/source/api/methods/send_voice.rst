#########
sendVoice
#########

Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as Audio or Document). On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_voice
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_voice(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendVoice`
- :code:`from aiogram.api.methods import SendVoice`
- :code:`from aiogram.api.methods.send_voice import SendVoice`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendVoice(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendVoice(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendVoice(...)