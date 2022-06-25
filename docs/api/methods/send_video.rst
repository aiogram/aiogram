#########
sendVideo
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_video
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_video(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_video import SendVideo`
- alias: :code:`from aiogram.methods import SendVideo`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendVideo(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendVideo(...)
