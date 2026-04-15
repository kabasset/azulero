Batch processing
================

Introduction
------------

Starting from version 2.0, when executed as part of a Unix or Windows pipeline,
Azulero commands can read their arguments from the standard input stream (``stdin``),
and write their results to the standard output stream (``stdout``),
while logs are written to the standard error stream (``stderr``).
Moreover, the commands now accept multiple inputs,
which make them suitable for batch processing.

For example, the following Unix pipeline will find and download MER data for a collection of targets,
render color images for each target, and display them:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 --radius 1m | azul process | xargs open

Note that several tiles may contain each source, such that more than two images may be rendered.

In this page, we'll dissect this example line and explain the message flow.
For the sake of simplicity (and sanity), we'll illustrate the features for Unix systems only.
Translation to Windows is left as an exercise!

Workdirs
--------

The output of ``azul retrieve`` and the input of ``azul process``
is a list of workdir paths relative to the parent workspace.
If they are not provided to the ``process`` command line, they will be read from ``stdin``.

Let's decompose the example command as:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 --radius 1m > workdirs.txt
   azul process < workdirs.txt

Typically, ``workdirs.txt`` would contain something like::

   102158889/NGC6505
   102159776/UGC11116


Renders
-------

The paths to images rendered by the last step of ``azul process`` are forwarded to ``stdout``.
They are relative to the workspace.

For example, ``azul process 102158889/NGC6505 102159776/UGC11116`` would output::

   102158889/NGC6505/NGC6505_102158889_adjusted.tiff
   102159776/UGC11116/UGC11116_102159776_adjusted.tiff


Catalogs
--------

Let us now go further!
In the introduction, ``azul retrieve`` took its targets from the command line.
If no target is provided this way, however, the command will read ``stdin``.

For example, consider a file ``target.txt`` containing::

   NGC6505
   UGC11116

Then:

.. prompt:: bash

   azul retrieve --radius 1m < targets.txt

will consider each word of ``targets.txt`` as a target
and retrieve the corresponding data.

A more realistic example would be the use of a catalog file.
For simplicity, let us assume the targets are stored in some CSV file ``catalog.csv``,
which starts as follows:

====== ====== ======
ra     dec    NGC
====== ====== ======
267.78 65.53  6505
270.93 67.05
...    ...    ...
====== ====== ======

We will select a range of rows (say, 2 and 3) with ``sed``,
and the ``ra`` and ``dec`` columns with ``cut``,
and pass the result to Azulero:

.. prompt:: bash

   sed -n '2,3p' catalog.csv | cut -d ',' -f 1,2 | azul retrieve


Named options
-------------

Named options like ``--workspace`` are not forwarded through pipelines.
Therefore, we have implemented an environment-level mechanism in order to avoid repeating them from command to command.
Each named option can be read from an environment variable named as follows:

.. code-block:: xml

   AZUL<COMMAND>_<OPTION>

where:

* ``<COMMAND>`` is the uppercase command name, if any, such as ``RETRIEVE`` or ``PROCESS``;
* ``<OPTION>`` is the uppercase long-from option name, such as ``FROM`` for ``--from``
  or ``WHITE`` for ``--white`` (but not ``W`` for ``-w``).

For example:

.. prompt:: bash

   export AZUL_LOG=DEBUG
   export AZULRETRIEVE_FROM=pdr
   export AZULRETRIEVE_RADIUS=1m

sets the log level to ``DEBUG`` for all commands,
and sets the data provider to ``pdr`` and crop radius to 1 arcmin for ``azul retrieve``.
These parameters are overloaded by command line arguments.

With this context, the following lines are equivalent:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 | azul process
   azul --log DEBUG retrieve NGC6505 UGC11116 --radius 1m --from pdr -f | azul --log DEBUG process