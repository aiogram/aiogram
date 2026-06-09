.. _magic-filters:

=============
Magic filters
=============

.. note::

    This page still in progress. Has many incorrectly worded sentences.

Is external package maintained by *aiogram* core team.

By default installs with *aiogram* and also is available on `PyPi - magic-filter <https://pypi.org/project/magic-filter/>`_.
That's mean you can install it and use with any other libraries and in own projects without depending *aiogram* installed.

Usage
=====

The **magic_filter** package implements class shortly named :class:`magic_filter.F` that's mean :code:`F` can be imported from :code:`aiogram` or :code:`magic_filter`. :class:`F` is alias for :class:`MagicFilter`.

.. note::

    Note that *aiogram* has an small extension over magic-filter and if you want to use this extension you should import magic from *aiogram* instead of *magic_filter* package

The :class:`MagicFilter` object is callable, supports :ref:`some actions <magic-filter-possible-actions>`
and memorize the attributes chain and the action which should be checked on demand.

So that's mean you can chain attribute getters, describe simple data validations
and then call the resulted object passing single object as argument,
for example make attributes chain :code:`F.foo.bar.baz` then add
action ':code:`F.foo.bar.baz == 'spam'` and then call the resulted object - :code:`(F.foo.bar.baz == 'spam').resolve(obj)`

.. _magic-filter-possible-actions:

Possible actions
================

Magic filter object supports some of basic logical operations over object attributes

Exists or not None
------------------

Default actions.

.. code-block:: python

    F.photo  # lambda message: message.photo

Equals
------

.. code-block:: python

    F.text == 'hello'  # lambda message: message.text == 'hello'
    F.from_user.id == 42  # lambda message: message.from_user.id == 42
    F.text != 'spam'  # lambda message: message.text != 'spam'

Is one of
---------

Can be used as method named :code:`in_` or as matmul operator :code:`@` with any iterable

.. code-block:: python

    F.from_user.id.in_({42, 1000, 123123})  # lambda query: query.from_user.id in {42, 1000, 123123}
    F.data.in_({'foo', 'bar', 'baz'})  # lambda query: query.data in {'foo', 'bar', 'baz'}

Contains
--------

.. code-block:: python

    F.text.contains('foo')  # lambda message: 'foo' in message.text

String startswith/endswith
--------------------------

Can be applied only for text attributes

.. code-block:: python

    F.text.startswith('foo')  # lambda message: message.text.startswith('foo')
    F.text.endswith('bar')  # lambda message: message.text.startswith('bar')

Regexp
------

.. code-block:: python

    F.text.regexp(r'Hello, .+')  # lambda message: re.match(r'Hello, .+', message.text)

Custom function
---------------

Accepts any callable. Callback will be called when filter checks result

.. code-block:: python

    F.chat.func(lambda chat: chat.id == -42)  # lambda message: (lambda chat: chat.id == -42)(message.chat)

Inverting result
----------------

Any of available operation can be inverted by bitwise inversion - :code:`~`

.. code-block:: python

    ~F.text  # lambda message: not message.text
    ~F.text.startswith('spam')  # lambda message: not message.text.startswith('spam')

Combining
---------

All operations can be combined via bitwise and/or operators - :code:`&`/:code:`|`

.. code-block:: python

    (F.from_user.id == 42) & (F.text == 'admin')
    F.text.startswith('a') | F.text.endswith('b')
    (F.from_user.id.in_({42, 777, 911})) & (F.text.startswith('!') | F.text.startswith('/')) & F.text.contains('ban')


Attribute modifiers - string manipulations
------------------------------------------

Make text upper- or lower-case

Can be used only with string attributes.

.. code-block:: python

    F.text.lower() == 'test'  # lambda message: message.text.lower() == 'test'
    F.text.upper().in_({'FOO', 'BAR'})  # lambda message: message.text.upper() in {'FOO', 'BAR'}
    F.text.len() == 5  # lambda message: len(message.text) == 5


Get filter result as handler argument
-------------------------------------

This part is not available in *magic-filter* directly but can be used with *aiogram*

.. code-block:: python

    from aiogram import F

    ...

    @router.message(F.text.regexp(r"^(\d+)$").as_("digits"))
    async def any_digits_handler(message: Message, digits: Match[str]):
        await message.answer(html.quote(str(digits)))

Usage in *aiogram*
==================

.. code-block:: python

    @router.message(F.text == 'hello')
    @router.inline_query(F.data == 'button:1')
    @router.message(F.text.startswith('foo'))
    @router.message(F.content_type.in_({'text', 'sticker'}))
    @router.message(F.text.regexp(r'\d+'))

    ...

    # Many others cases when you will need to check any of available event attribute
