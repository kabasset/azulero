Batch processing
================

Introduction
------------

Starting from version 2.0, when executed as part of a Unix or Windows pipeline,
Azulero commands can read their positional arguments from the standard input stream (``stdin``),
and write their results to the standard output stream (``stdout``),
while logs are written to the standard error stream (``stderr``).
Moreover, the commands now accept multiple inputs,
which make them suitable for batch processing.

For example, the following pipeline will find and download MER data for a collection of (two) targets,
and then render color images for each target:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 --radius 1m | azul process

Note that several MER tiles may contain each of the targets,
such that more than two images may be rendered.

Next section dissects this example line to explain the communication flow,
and following sections show related features for even more fun with pipelines!
Basic knowledge on pipelines and standard streams
-- specifically, knowing operators ``|``, ``<`` and ``>`` -- is required.
For the sake of simplicity (and sanity), we'll illustrate the features for Unix systems only.
Translation to Windows is left as an exercise!


..  _workspace:

Workdirs
--------

The output of ``azul retrieve`` and the input of ``azul process``
is a list of workdir paths relative to some parent workspace.
If they are not provided to the ``azul process`` command line, they will be read from ``stdin``.

If we decompose the example by introducing an intermediate file with:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 --radius 1m > workdirs.txt

the said intermediate file will contain one workdir per line::

   102158889/NGC6505
   102159776/UGC11116

Each of them is then taken as input by ``azul process`` in:

.. prompt:: bash

   azul process < workdirs.txt


Renders
-------

The paths to images rendered by ``azul process`` are forwarded to ``stdout``.
They are relative to the workspace.

For example:

.. prompt:: bash

   azul process 102158889/NGC6505 102159776/UGC11116 > renders.txt

would write::

   102158889/NGC6505/NGC6505_102158889_adjusted.tiff
   102159776/UGC11116/UGC11116_102159776_adjusted.tiff

Generally, ``azul process`` creates several files per workdir: one per active step.
Only the path to the last step output (by default, ``adjusted``) is returned.


Catalogs
--------

Let us now go further!
In the introduction, ``azul retrieve`` took its targets from the command line.
If no targets were provided this way, however, the command would have read ``stdin``.

Consider a file ``target.txt`` containing::

   NGC6505
   UGC11116

Then:

.. prompt:: bash

   azul retrieve --radius 1m < targets.txt

will treat each word of ``targets.txt`` as a target
and retrieve the corresponding data.

A more realistic (and useful) example would be to rely on a catalog file.
Let us assume the target coordinates are stored in some CSV file ``catalog.csv``,
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
and finally pass the result to Azulero:

.. prompt:: bash

   sed -n '2,3p' catalog.csv | cut -d ',' -f 1,2 | azul retrieve


..  _named_options:

Named options
-------------

Named options like ``--workspace`` are not forwarded through pipelines.
Typically, the following pipeline would break:

.. prompt:: bash

   azul --workspace /tmp retrieve NGC6505 | azul process

because ``azul process`` would use the default workspace (``.``)
instead of the custom workspace given to ``azul retrieve``.

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

Within this context, the following lines are equivalent:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 | azul process
   azul --log DEBUG retrieve NGC6505 UGC11116 --radius 1m --from pdr -f | azul --log DEBUG process


All-in-one pipeline
-------------------

In one command line, we are now able to:

* Read a catalog;
* Retrieve MER cutouts;
* Render color images for each cutout.

We will now:

* Render in parallel;
* Open the color images as they come out.

with targets in the command line:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 --radius 1m | \
     xargs -n1 -P0 azul process | \
     xargs -n1 open

or with targets from a catalog:

.. prompt:: bash

   sed -n '2,3p' catalog.csv | cut -d ',' -f 1,2 | \
     azul retrieve --radius 1m | \
     xargs -n1 -P0 azul process | \
     xargs -n1 open
 
Voilà!
