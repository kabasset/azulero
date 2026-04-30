Pipelines
=========

Introduction
------------

Starting from version 2.0, when executed as part of a Unix or Windows pipeline,
Azulero commands can read their positional arguments from the standard input stream (``stdin``),
and write their results to the standard output stream (``stdout``),
while logs are written to the standard error stream (``stderr``).
Moreover, the commands now accept multiple inputs,
which make them suitable for batch processing.

The following sections demonstrate classical use cases.
Basic knowledge on pipelines and standard streams
-- specifically, knowing operators ``|``, ``<`` and ``>`` -- is required.
For the sake of simplicity (and sanity), we'll illustrate the features for Bash on Unix systems only.
Translation to Windows is left as an exercise!

The results will be presented for public Q1 data only;
set the following environment variables in order to reproduce the images exactly:

.. prompt:: bash

   export AZULRETRIEVE_FROM=pdr
   export AZULRETRIEVE_DSR=Q1_R1


Object names to color images
----------------------------

The simplest use case for an Azulero pipeline is to download MER data and render color images.
In this example, we will use galaxy names as input:

.. prompt:: bash

   azul retrieve UGC11116 PGC61356 --radius 1m | azul process

Note that several MER tiles may contain a given target,
such that more than two images may be rendered.
If this is unwanted, set option ``-n 1``.
Conversely, several targets may belong the same tile,
which is the case for those two galaxies in `Q1 tile 102159776 <https://www.youtube.com/watch?v=z1-V0zz4p_s>`_.

The above command will generate two images:

.. subfigure:: AB
   :gap: 1em

   .. image:: _static/UGC11116_102159776_azul_adjusted.jpg

   .. image:: _static/PGC61356_102159776_azul_adjusted.jpg

   2' x 2' cutouts around UGC11116 and PGC61356.
   Credit: ESA Euclid/Euclid Consortium/NASA/Q1-2025/Antoine Basset (CNES)

The resulting workspace contains two workdirs which share a common tile folder::

   102159776
   ├── PGC61356
   │   ├── EUC_MER_BGSUB-MOSAIC-NIR-H_TILE102159776-9A9A41_20241024T223843.133644Z_00.00.fits
   │   ├── EUC_MER_BGSUB-MOSAIC-NIR-J_TILE102159776-A30311_20241024T223448.200678Z_00.00.fits
   │   ├── EUC_MER_BGSUB-MOSAIC-NIR-Y_TILE102159776-F70908_20241024T222851.359405Z_00.00.fits
   │   ├── EUC_MER_BGSUB-MOSAIC-VIS_TILE102159776-ACB359_20241025T034718.289475Z_00.00.fits
   │   ├── PGC61356_102159776_azul_adjusted.tiff
   │   ├── PGC61356_102159776_azul_blended.tiff
   │   ├── PGC61356_102159776_azul_mask.tiff
   │   └── PGC61356_102159776_azul_wcs.yaml
   └── UGC11116
      ├── EUC_MER_BGSUB-MOSAIC-NIR-H_TILE102159776-9A9A41_20241024T223843.133644Z_00.00.fits
      ├── EUC_MER_BGSUB-MOSAIC-NIR-J_TILE102159776-A30311_20241024T223448.200678Z_00.00.fits
      ├── EUC_MER_BGSUB-MOSAIC-NIR-Y_TILE102159776-F70908_20241024T222851.359405Z_00.00.fits
      ├── EUC_MER_BGSUB-MOSAIC-VIS_TILE102159776-ACB359_20241025T034718.289475Z_00.00.fits
      ├── UGC11116_102159776_azul_adjusted.tiff
      ├── UGC11116_102159776_azul_blended.tiff
      ├── UGC11116_102159776_azul_mask.tiff
      └── UGC11116_102159776_azul_wcs.yaml

We have generated the color images one after the other by executing a single ``azul process`` command,
but it is possible to parallelize the pipeline, for example with xargs:

.. prompt:: bash

   azul retrieve UGC11116 PGC61356 --radius 1m | xargs -n 1 -P 4 azul process

where ``-n 1`` is the number of targets passed to each ``azul process`` command,
and ``-P 4`` is the maximum number of parallel executions.

Similarly, the retrieval can be parallelized:

.. prompt:: bash

   echo UGC11116 PGC61356 | xargs -n 1 -P 4 azul retrieve --radius 1m | xargs -n 1 -P 4 azul process

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

Online catalog to collage
-------------------------

Let us run Azulero on the lens catalog which was used to render
`the Q1 strong lensing collage <https://www.esa.int/ESA_Multimedia/Images/2025/03/Strong_gravitational_lenses_captured_by_Euclid>`_
to generate a similar output in one pipeline:

.. prompt:: bash

   wget -q -O - https://zenodo.org/records/15025832/files/q1_discovery_engine_lens_catalog.csv \
   | tail -n+2 \
   | sort -r -t ',' -k 8 \
   | head -112 \
   | cut -d ',' -f 5,6 \
   | azul retrieve -n 1 --radius 5s \
   | azul process \
   | azul arrange -n 14 \
   | xargs open 

The above pipeline performs the following:

* download the catalog into ``stdout``,
* remove the header row,
* sort rows by descending flux,
* select RA and Dec columns,
* keep 14 x 8 = 112 targets,
* retrieve one 10" x 10" cutout per target,
* render a color image per cutout,
* arrange renders into a 14-column grid,
* display the resulting collage:

.. figure:: _static/collage_56.46762095259402,-49.45093443791871_102020055_azul_adjusted_56.46762095259402,-49.45093443791871_102020055_azul_adjusted.png

   Collage of 10" x 10" cutouts around Q1 srong lenses.
   Credit: ESA Euclid/Euclid Consortium/NASA/Q1-2025/Antoine Basset (CNES)
