#########
sendVideo
#########

Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as Document). On success, the sent Message is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_video
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_video(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendVideo`
- :code:`from aiogram.api.methods import SendVideo`
- :code:`from aiogram.api.methods.send_video import SendVideo`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendVideo(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendVideo(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendVideo(...)