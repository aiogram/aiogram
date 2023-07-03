##############
editForumTopic
##############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_forum_topic
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_forum_topic(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_forum_topic import EditForumTopic`
- alias: :code:`from aiogram.methods import EditForumTopic`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditForumTopic(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditForumTopic(...)
