######################
Command line interface
######################

aiogram ships an ``aiogram`` command. ``python -m aiogram`` runs the same CLI. It is built on the
standard library ``argparse`` and needs no extra packages. It replaces the separate ``aiogram-cli``
package and the ``aiogram[cli]`` extra.

.. code-block:: console

    $ aiogram --help
    $ aiogram --version

Root options (before the command): ``--version``, and ``--traceback`` to print the full traceback
of an error.

Commands
========

``aiogram info [--json]``
    Versions and build details, ready to paste into a bug report: aiogram, the Rust core build
    (version, profile, target), Python version and implementation, whether the build is
    free-threaded and whether the GIL is enabled, the wheel tag, and the **installed optional
    packages** with their versions. Installation metadata does not record which extras were
    requested, so the list shows every package an extra can pull in that is installed.

    ``--json`` prints an object with the keys ``aiogram``, ``core``, ``python``,
    ``implementation``, ``free_threaded``, ``gil_enabled``, ``wheel_tag`` and
    ``installed_optional_packages``. ``core`` is ``null`` when the Rust core fails to load.

``aiogram migrate check PATH...`` / ``aiogram migrate fix PATH...``
    Checks or rewrites aiogram 3.x code for 4.0. Needs ``pip install 'aiogram[migrate]'``.

Exit codes
==========

=====  ==============================================
``0``  success
``1``  runtime error
``2``  usage error (unknown command, bad arguments)
``3``  findings (``aiogram migrate check``)
=====  ==============================================

Bot token
=========

Commands that call the Bot API read the token from ``$BOT_TOKEN`` or ``--token-file PATH``.
``--token TOKEN`` is accepted too, with a warning: a token on the command line ends up in shell
history. The CLI never prints the token and masks it in error messages (``123456:***``).

Colours
=======

Output is coloured only on a terminal, and never when the ``NO_COLOR`` environment variable is
set to a non-empty value.

Plugins
=======

A package adds commands through the ``aiogram.cli`` entry-point group:

.. code-block:: toml

    [project.entry-points."aiogram.cli"]
    hello = "aiogram_hello:register"

.. code-block:: python

    import argparse


    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser("hello", help="say hello")
        parser.add_argument("--name", default="world")
        parser.set_defaults(func=hello)


    def hello(args: argparse.Namespace) -> int | None:
        print(f"hello, {args.name}")
        return 0  # the exit code; None means 0

A handler can raise ``aiogram.cli.CliError(message, exit_code=...)`` to exit with a message and
no traceback. Any other exception prints ``aiogram: error: <type>: <message>`` and exits with
``1``.

- A plugin that fails to import or to register is reported on stderr with its entry-point and
  distribution name. Other commands keep working.
- Built-in commands always win over plugin commands with the same name or alias. Between plugins,
  the first in sorted entry-point-name order wins. Every collision prints a warning naming both
  sides.
