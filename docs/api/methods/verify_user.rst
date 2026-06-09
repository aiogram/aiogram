##########
verifyUser
##########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.verify_user
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.verify_user(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.verify_user import VerifyUser`
- alias: :code:`from aiogram.methods import VerifyUser`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(VerifyUser(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return VerifyUser(...)
