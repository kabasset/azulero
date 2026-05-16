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
   Optional global arguments (e.g. ``--log DEBUG``).
``<command>``
   The name of the command (e.g. ``retrieve``).
``<input>``
   The space separated list of inputs (e.g. ``UGC11116 PGC61356``).
   If the list is empty, then ``stdin`` is read (see next section and :doc:`pipelines`).
``[options]``
   Optional command arguments (e.g. ``-r 1m``).

Global options, common to all commands, are passed *between* ``azul`` and the command name,
and command options are passed *after* the command name, before or after inputs.
Option ``-o <output>`` exists for all commands.

Here is an example command line with global and command options,
a list of inputs and an output specification:

.. prompt:: bash

   azul --log DEBUG retrieve -r 1m -n 1 UGC11116 PGC61356 -o {target}


.. _workspace:

Workspace, input and output paths
---------------------------------

Azulero defines three types of directories:

Workspace
   A parent directory under which all inputs and outputs are located by default.
Tiledirs
   Directories inside the workspace which contain data for a single tile.
   Tiledirs are named after the tile index.
Workdirs
   Directories inside the workspace, generally inside tiledirs, which contain data for a single target.

By default, all paths passed as input of a command are assumed to be relative to the workspace,
unless they are absolute paths.
Output paths are specified as templates with curly brace-enclosed placeholders.
The placeholders are replaced with values depending on the command parameters.
For example, most output path start with placeholder ``{workspace}``,
which will be rendered as the actual workspace path.


Global options
--------------

Global options are:

``--log``
   The log level, either ``DEBUG``, ``INFO`` (the default), ``WARNING`` or ``ERROR``.
``--workspace``
   The path to the workspace.
   Defaults to the current directory.
``--channels``
   The way the four Euclid bands are uniquely identified in the paths to MER data, e.g. ``NIR-J``.
   Unless you generate MER-like data yourself, you should not use this option.
``--input``
   The glob pattern used to find Euclid bands in a workdir.
   It must contain placeholder ``{channel}``, which is rendered accordingly to the values of option ``--channels``.
   For example, ``*_{channel}_*.fits`` would accept files with ``.fits`` extension
   which contain the band name (e.g. ``NIR-J``) separated from other chunks by underscores.


Standard streams
----------------

Azulero commands read and write different types of messages from and to the different standard streams:

``stdin``
   When no inputs are provided to the command line, they are read from ``stdin``.
   If ``stdin`` is also empty, then the command stops early.
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
   The uppercase *long-from* option name, such as ``FROM`` for ``--from``
   or ``RADIUS`` for ``--radius`` but not ``R`` for ``-r``.

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
