Installation Guide
==================

Using PIP
---------
    .. code-block:: bash

        $ pip install -U aiogram

Using AUR
---------
*aiogram* is also available in Arch User Repository, so you can install this library on any Arch-based distribution like ArchLinux, Antergos, Manjaro, etc. To do this, use your favorite AUR-helper and install `python-aiogram <https://aur.archlinux.org/packages/python-aiogram/>`_ package.

From sources
------------
    .. code-block:: bash

        $ git clone https://github.com/aiogram/aiogram.git
        $ cd aiogram
        $ python setup.py install

    or if you want to install development version (maybe unstable):

    .. code-block:: bash

        $ git clone https://github.com/aiogram/aiogram.git
        $ cd aiogram
        $ git checkout dev-2.x
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

In addition, you don't need do nothing, *aiogram* is automatically starts using that if is found in your environment.
