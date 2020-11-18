#########
sendAudio
#########

Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent Message is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.

For sending voice messages, use the sendVoice method instead.

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_audio
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_audio(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendAudio`
- :code:`from aiogram.methods import SendAudio`
- :code:`from aiogram.methods.send_audio import SendAudio`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendAudio(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendAudio(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendAudio(...)