##########
verifyChat
##########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.verify_chat
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.verify_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.verify_chat import VerifyChat`
- alias: :code:`from aiogram.methods import VerifyChat`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(VerifyChat(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return VerifyChat(...)
