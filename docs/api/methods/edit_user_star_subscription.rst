########################
editUserStarSubscription
########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_user_star_subscription
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_user_star_subscription(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_user_star_subscription import EditUserStarSubscription`
- alias: :code:`from aiogram.methods import EditUserStarSubscription`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditUserStarSubscription(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditUserStarSubscription(...)
