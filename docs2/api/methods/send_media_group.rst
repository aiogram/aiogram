##############
sendMediaGroup
##############

Use this method to send a group of photos or videos as an album. On success, an array of the sent Messages is returned.

Returns: :obj:`List[Message]`

.. automodule:: aiogram.methods.send_media_group
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: List[Message] = await bot.send_media_group(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendMediaGroup`
- :code:`from aiogram.methods import SendMediaGroup`
- :code:`from aiogram.methods.send_media_group import SendMediaGroup`

In handlers with current bot
----------------------------

.. code-block::

    result: List[Message] = await SendMediaGroup(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: List[Message] = await bot(SendMediaGroup(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendMediaGroup(...)