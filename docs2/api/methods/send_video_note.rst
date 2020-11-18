#############
sendVideoNote
#############

As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_video_note
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_video_note(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendVideoNote`
- :code:`from aiogram.methods import SendVideoNote`
- :code:`from aiogram.methods.send_video_note import SendVideoNote`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendVideoNote(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendVideoNote(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendVideoNote(...)