###########
repostStory
###########

Returns: :obj:`Story`

.. automodule:: aiogram.methods.repost_story
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Story = await bot.repost_story(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.repost_story import RepostStory`
- alias: :code:`from aiogram.methods import RepostStory`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Story = await bot(RepostStory(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RepostStory(...)
