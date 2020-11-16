#############
sendAnimation
#############

Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent Message is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_animation
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_animation(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendAnimation`
- :code:`from aiogram.api.methods import SendAnimation`
- :code:`from aiogram.api.methods.send_animation import SendAnimation`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendAnimation(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendAnimation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendAnimation(...)