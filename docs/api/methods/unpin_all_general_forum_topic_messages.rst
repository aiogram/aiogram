#################################
unpinAllGeneralForumTopicMessages
#################################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.unpin_all_general_forum_topic_messages
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.unpin_all_general_forum_topic_messages(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.unpin_all_general_forum_topic_messages import UnpinAllGeneralForumTopicMessages`
- alias: :code:`from aiogram.methods import UnpinAllGeneralForumTopicMessages`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(UnpinAllGeneralForumTopicMessages(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return UnpinAllGeneralForumTopicMessages(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.unpin_all_general_forum_topic_messages`
