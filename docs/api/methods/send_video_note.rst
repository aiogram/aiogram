#############
sendVideoNote
#############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_video_note
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.send_video_note import SendVideoNote`
- alias: :code:`from aiogram.methods import SendVideoNote`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Message = await SendVideoNote(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendVideoNote(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendVideoNote(...)
