#########
sendVenue
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_venue
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_venue(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_venue import SendVenue`
- alias: :code:`from aiogram.methods import SendVenue`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendVenue(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendVenue(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_venue`
- :meth:`aiogram.types.message.Message.reply_venue`
