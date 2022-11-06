################
createForumTopic
################

Returns: :obj:`ForumTopic`

.. automodule:: aiogram.methods.create_forum_topic
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: ForumTopic = await bot.create_forum_topic(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.create_forum_topic import CreateForumTopic`
- alias: :code:`from aiogram.methods import CreateForumTopic`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ForumTopic = await bot(CreateForumTopic(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CreateForumTopic(...)
