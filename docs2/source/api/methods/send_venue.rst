#########
sendVenue
#########

Use this method to send information about a venue. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_venue
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_venue(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendVenue`
- :code:`from aiogram.api.methods import SendVenue`
- :code:`from aiogram.api.methods.send_venue import SendVenue`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendVenue(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendVenue(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendVenue(...)