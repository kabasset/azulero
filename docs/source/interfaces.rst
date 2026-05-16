General interface design
========================

Introduction
------------

TODO

Commands
--------

The main script is ``azul``.
It supports a variety of so-called **commands**,
such as ``retrieve`` to download datafiles or ``process`` to render color images.
All commands follow the same pattern::

   azul [global_options] <command> <inputs> [options]

with:

``[global_options]``
   Optional global options (e.g. ``--log DEBUG``).
``<command>``
   The name of the command (e.g. ``retrieve``).
``<input>``
   The space separated list of inputs (e.g. ``UGC11116 PGC61356``).
   If the list is empty, then ``stdin`` is read (see next section and :doc:`pipelines`).
``[options]``
   The command options (e.g. ``-r 1m``).

Global options, common to all commands, are passed *between* ``azul`` and the command name,
and command options are passed *after* the command name, before or after inputs.
Option ``-o <output>`` exists for all commands.

Here is an example command line with global and command options,
a list of inputs and an output specification:

.. prompt:: bash

   azul --log DEBUG retrieve -r 1m UGC11116 PGC61356 -o {target}


Standard streams
----------------

Azulero passes various messages via standard streams:

``stdin``
   When no inputs are provided to the command line, they are read from ``stdin``.
   If ``stdin`` is empty, then the command stops early.
``stdout``
   The results of the command (e.g. path to workdir or rendered image) are written to ``stdout``
   for further use by commands down a pipeline.
``stderr``
   Azulero commands log to ``stderr``.

For more details, see :doc:`pipelines`.


..  _named_options:

Named options
-------------

For pipelining and batch processing, Azulero offers an environment-level mechanism
for setting named options like global option ``--log`` or :doc:`retrieve` option ``--from``.
Each named option can be read from an environment variable named as follows:

.. code-block:: xml

   AZUL<COMMAND>_<OPTION>

with:

``<COMMAND>``
   The uppercase command name, if any, such as ``RETRIEVE`` or ``PROCESS``,
   or nothing for global options.
``<OPTION>``
   The uppercase long-from option name, such as ``FROM`` for ``--from``
   or ``WHITE`` for ``--white`` (but not ``W`` for ``-w``).

For example:

.. prompt:: bash

   export AZUL_LOG=DEBUG
   export AZULRETRIEVE_FROM=pdr
   export AZULRETRIEVE_RADIUS=1m

sets the log level to ``DEBUG`` for all commands,
and sets the data provider to ``pdr`` and crop radius to 1 arcmin for :doc:`retrieve`.
These parameters are overloaded by command line arguments.

Within this context, the following lines are equivalent:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 | azul process
   azul --log DEBUG retrieve NGC6505 UGC11116 -r 1m --from pdr -f | azul --log DEBUG process
