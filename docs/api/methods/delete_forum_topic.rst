################
deleteForumTopic
################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_forum_topic
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_forum_topic(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_forum_topic import DeleteForumTopic`
- alias: :code:`from aiogram.methods import DeleteForumTopic`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteForumTopic(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteForumTopic(...)
