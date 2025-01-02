######################
removeUserVerification
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.remove_user_verification
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.remove_user_verification(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.remove_user_verification import RemoveUserVerification`
- alias: :code:`from aiogram.methods import RemoveUserVerification`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(RemoveUserVerification(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RemoveUserVerification(...)
