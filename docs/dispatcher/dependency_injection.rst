####################
Dependency injection
####################

Dependency injection is a programming technique that makes a class independent of its dependencies. It achieves that by decoupling the usage of an object from its creation. This helps you to follow `SOLID's <https://en.wikipedia.org/wiki/SOLID>`_ dependency inversion and single responsibility principles.


How it works in aiogram
=======================
For each update :class:`Dispatcher` passes handling context data. Filters and middleware can also make changes to the context.

To access contextual data you should specify corresponding keyword parameter in handler or filter. For example, to get :class:`FSMContext` we do it like that:

.. code-block:: python
    @router.message(ProfileCompletion.add_photo, F.photo)
    async def add_photo(
        message: types.Message, bot: Bot, state: FSMContext
    ) -> Any:
        ... # do something with photo


Injecting own dependencies
==========================

Aiogram provides several ways to complement / modify contextual data.

The first and easiest way is to simply specify the named arguments in :class:`Dispatcher` initialization, polling start methods or :class:`SimpleRequestHandler` initialization if you use webhooks.

.. code-block:: python
    async def main() -> None:
        dp = Dispatcher(..., foo=42)
        return await dp.start_polling(
            bot, allowed_updates=dp.resolve_used_update_types(), bar="Bazz"
        )
Analogy for webhook:

.. code-block:: python
    async def main() -> None:
        dp = Dispatcher(..., foo=42)
        handler = SimpleRequestHandler(dispatcher=dp, bot=bot, bar="Bazz")
        ... # starting webhook
:class:`Dispatcher`'s workflow data also can be supplemented by setting values as in a dictionary:

.. code-block:: python
    dp = Dispatcher(...)
    dp["eggs"] = Spam()
The middlewares updates the context quite often.
You can read more about them on this page:

- `Middlewares <middlewares.html>`__

The last way is to return a dictionary from the filter:

.. literalinclude:: ../../../examples/context_addition_from_filter.py

...or using MagicFilter with :code:`as_()` method. (`Read more <filters/magic_filters.html#get-filter-result-as-handler-argument>`__)
