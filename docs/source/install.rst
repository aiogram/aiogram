Installation Guide
==================

Using PIP
---------
    .. code-block:: bash

        $ pip install -U aiogram

Using Pipenv
------------
    .. code-block:: bash

        $ pipenv install aiogram

Using AUR
---------
*aiogram* is also available in Arch User Repository, so you can install this library on any Arch-based distribution like ArchLinux, Antergos, Manjaro, etc. To do this, use your favorite AUR-helper and install `python-aiogram <https://aur.archlinux.org/packages/python-aiogram/>`_ package.

From sources
------------

    Development versions:

    .. code-block:: bash

        $ git clone https://github.com/aiogram/aiogram.git
        $ cd aiogram
        $ python setup.py install

    Or if you want to install stable version (The same with version form PyPi):

    .. code-block:: bash

        $ git clone https://github.com/aiogram/aiogram.git
        $ cd aiogram
        $ git checkout master
        $ python setup.py install


Recommendations
---------------
You can speedup your bots by following next instructions:

- Use `uvloop <https://github.com/MagicStack/uvloop>`_ instead of default asyncio loop.

    *uvloop* is a fast, drop-in replacement of the built-in asyncio event loop. uvloop is implemented in Cython and uses libuv under the hood.

    **Installation:**

        .. code-block:: bash

            $ pip install uvloop

- Use `ujson <https://github.com/esnme/ultrajson>`_ instead of default json module.

    *UltraJSON* is an ultra fast JSON encoder and decoder written in pure C with bindings for Python 2.5+ and 3.

    **Installation:**

        .. code-block:: bash

            $ pip install ujson

- Use aiohttp speedups

    - Use `cchardet <https://github.com/PyYoshi/cChardet>`_ instead of chardet module.

        *cChardet* is high speed universal character encoding detector.

        **Installation:**

            .. code-block:: bash

                $ pip install cchardet

    - Use `aiodns <https://github.com/saghul/aiodns>`_ for speeding up DNS resolving.

        *aiodns* provides a simple way for doing asynchronous DNS resolutions.

        **Installation:**

            .. code-block:: bash

                $ pip install aiodns

    - Installing speedups altogether.

        The following will get you ``aiohttp`` along with ``cchardet,``, ``aiodns`` and ``brotlipy`` in one bundle.

        **Installation:**

            .. code-block:: bash

                $ pip install aiohttp[speedups]

In addition, you don't need do nothing, *aiogram* is automatically starts using that if is found in your environment.
