############
Installation
############

Stable (2.x)
============

Using PIP
---------

.. code-block:: bash

    pip install -U aiogram


Using poetry
------------

.. code-block:: bash

    poetry add aiogram


Using Pipenv
------------

.. code-block:: bash

    pipenv install aiogram

Using poetry
------------

.. code-block:: bash

    poetry add aiogram

Using Pacman
------------
*aiogram* is also available in Arch Linux Repository, so you can install this framework on any
Arch-based distribution like Arch Linux, Antergos, Manjaro, etc. To do this, just use pacman
to install the `python-aiogram <https://archlinux.org/packages/community/any/python-aiogram/>`_ package:

.. code-block:: bash

    pacman -S python-aiogram

Development build (3.x)
=======================

From private PyPi index
-----------------------

On every push to the `dev-3.x` branch GitHub Actions build the package and publish
to the `2038.host <https://aiogram.2038.io/simple>`_ server with seems like official PyPi files structure.
That's mean you can always install latest (may be unstable) build via next command:

.. code-block:: bash

    pip install --extra-index-url https://dev-docs.aiogram.dev/simple --pre aiogram


In this repository available only last success build. All previous builds is always removes
before uploading new one. Also before building this package all tests is also pass.
