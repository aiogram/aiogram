############
Installation
############

From PyPI
---------

.. code-block:: bash

    pip install -U aiogram

No wheel for your platform
~~~~~~~~~~~~~~~~~~~~~~~~~~

aiogram 4 contains a compiled core (``aiogram._core``), so a wheel fits one Python version and
platform. The 4.0 release wheels target CPython 3.11–3.15 and free-threaded 3.14t / 3.15t on Linux
(manylinux and musllinux, x86_64 and aarch64), macOS (x86_64 and arm64) and Windows x64.
PyPy is not supported.

Anywhere else pip falls back to the source distribution, which needs a Rust toolchain: the
version in ``rust-version`` of aiogram's ``Cargo.toml`` (currently Rust 1.98) or newer, for example
from `rustup <https://rustup.rs/>`_. On Termux, install Rust with ``pkg install rust``.

If ``import aiogram`` fails with *aiogram's compiled core is missing*, the installed copy has no
core for your interpreter: the message names the interpreter tag (``cp313``, ``cp314t``, ...)
and the platform the wheel has to match.

From Arch Linux Repository
--------------------------

.. warning:: Package in this repository may be outdated. Use PyPI package for the latest version.

.. code-block:: bash

    pacman -S python-aiogram

Development build
=================

From GitHub
-----------

.. code-block:: bash

    pip install https://github.com/aiogram/aiogram/archive/refs/heads/dev-3.x.zip
