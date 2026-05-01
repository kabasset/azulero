Pipelines
=========

Introduction
------------

Starting from version 2.0, when executed as part of a Unix or Windows pipeline,
Azulero commands can read their positional arguments from the standard input stream (``stdin``),
and write their results to the standard output stream (``stdout``).
Logs are written to the standard error stream (``stderr``).
Moreover, the commands now accept multiple inputs,
which make them suitable for batch processing.

The following sections demonstrate classical use cases.
Basic knowledge on pipelines and standard streams
-- specifically, knowing operators ``|``, ``<`` and ``>`` -- is required.
For the sake of simplicity (and sanity), we'll illustrate the features for Bash on Unix systems only.
Translation to Windows is left as an exercise!

For a better understanding of what actually happens,
the last section dissects the data flow of a simple pipeline.

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

   .. image:: _static/UGC11116_102159776_adjusted.jpg

   .. image:: _static/PGC61356_102159776_adjusted.jpg

   Color rendering of 2' x 2' cutouts around UGC11116 and PGC61356.
   Credit: ESA Euclid/Euclid Consortium/NASA/Q1-2025/Antoine Basset (CNES)

The resulting workspace contains two workdirs which share a common tile folder::

   102159776
   ├── PGC61356
   │   ├── EUC_MER_BGSUB-MOSAIC-NIR-H_TILE102159776-9A9A41_20241024T223843.133644Z_00.00.fits
   │   ├── EUC_MER_BGSUB-MOSAIC-NIR-J_TILE102159776-A30311_20241024T223448.200678Z_00.00.fits
   │   ├── EUC_MER_BGSUB-MOSAIC-NIR-Y_TILE102159776-F70908_20241024T222851.359405Z_00.00.fits
   │   ├── EUC_MER_BGSUB-MOSAIC-VIS_TILE102159776-ACB359_20241025T034718.289475Z_00.00.fits
   │   ├── PGC61356_102159776_adjusted.tiff
   │   ├── PGC61356_102159776_blended.tiff
   │   ├── PGC61356_102159776_mask.tiff
   │   └── PGC61356_102159776_wcs.yaml
   └── UGC11116
      ├── EUC_MER_BGSUB-MOSAIC-NIR-H_TILE102159776-9A9A41_20241024T223843.133644Z_00.00.fits
      ├── EUC_MER_BGSUB-MOSAIC-NIR-J_TILE102159776-A30311_20241024T223448.200678Z_00.00.fits
      ├── EUC_MER_BGSUB-MOSAIC-NIR-Y_TILE102159776-F70908_20241024T222851.359405Z_00.00.fits
      ├── EUC_MER_BGSUB-MOSAIC-VIS_TILE102159776-ACB359_20241025T034718.289475Z_00.00.fits
      ├── UGC11116_102159776_adjusted.tiff
      ├── UGC11116_102159776_blended.tiff
      ├── UGC11116_102159776_mask.tiff
      └── UGC11116_102159776_wcs.yaml

We have generated the color images one after the other by executing a single ``azul process`` command,
but it is possible to parallelize the pipeline, for example with ``xargs``:

.. prompt:: bash

   azul retrieve UGC11116 PGC61356 --radius 1m \
   | xargs -n 1 -P 4 azul process

where ``-n 1`` is the number of targets passed to each ``azul process`` command,
and ``-P 4`` is the maximum number of parallel executions.

Similarly, the retrieval can be parallelized:

.. prompt:: bash

   echo UGC11116 PGC61356 \
   | xargs -n 1 -P 4 azul retrieve --radius 1m \
   | xargs -n 1 -P 4 azul process


Online catalog to collage
-------------------------

Let us run Azulero on the lens catalog which was used to render
`the Q1 strong lensing collage <https://www.esa.int/ESA_Multimedia/Images/2025/03/Strong_gravitational_lenses_captured_by_Euclid>`_
and generate a similar output in one pipeline:

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
* arrange renderings into a 14-column grid,
* display the resulting collage:

.. figure:: _static/collage_56.46762095259402,-49.45093443791871_102020055_adjusted_56.46762095259402,-49.45093443791871_102020055_adjusted.png

   Collage of 10" x 10" cutouts around Q1 srong lenses.
   Credit: ESA Euclid/Euclid Consortium/NASA/Q1-2025/Antoine Basset (CNES)


Clipboard to slideshow
----------------------

FIXME nearby galaxies slideshow


Dissecting a pipeline
---------------------

Let us introduce a simple yet complete example pipeline:

.. prompt:: bash

   echo UGC11116 PGC61356 LEDA2697349 \
   | azul retrieve --radius 1m \
   | azul process \
   | azul arrange --format max \
   | xargs open

which gives:

.. figure:: _static/collage_UGC11116_102159776_adjusted_LEDA2697349_102159776_adjusted.png

   Collage of 2' x 2' cutouts around UGC11116, PGC61356 and LEDA2697349.
   Credit: ESA Euclid/Euclid Consortium/NASA/Q1-2025/Antoine Basset (CNES)

Since we did not pass option ``-n 1`` to ``azul retrieve``,
all of the tiles which contain a target are retrieved,
which is why there are two images of LEDA2697349.
One of them is incomplete because the whole 2' x 2' cutout doesn't fit inside the second tile.
With option ``-n``, the tiles would have been sorted by coverage in order to retrieve complete cutouts in priority.
Finally, ``azul arrange``'s option ``--format max`` is used to pad the smallest cutout instead of cropping the largest ones.

The message flow is illustrated below:

.. code::

     echo
    ┌─▼─────────────────────────────┐
    │ UGC11116 PGC61356 LEDA2697349 │
    └─▼─────────────────────────────┘
     azul retrieve
    ┌─▼─────────────────────┐
    │ 102159776/UGC11116    │
    │ 102159776/PGC61356    │
    │ 102160059/LEDA2697349 │
    │ 102159776/LEDA2697349 │
    └─▼─────────────────────┘
     azul process
    ┌─▼─────────────────────────────────────────────────────────┐
    │ 102159776/UGC11116/UGC11116_102159776_adjusted.tiff       │
    │ 102159776/PGC61356/PGC61356_102159776_adjusted.tiff       │
    │ 102160059/LEDA2697349/LEDA2697349_102160059_adjusted.tiff │
    │ 102159776/LEDA2697349/LEDA2697349_102159776_adjusted.tiff │
    └─▼─────────────────────────────────────────────────────────┘
     azul arrange
    ┌─▼──────────────────────────────────────────────────────────────────────┐
    │ collage_UGC11116_102159776_adjusted_LEDA2697349_102159776_adjusted.png │
    └─▼──────────────────────────────────────────────────────────────────────┘
     open

* ``echo`` streams the targets toward ``azul retrieve``.
* ``azul retrieve`` streams the workdirs toward ``azul process``.
* ``azul process`` streams the paths to the renderings toward ``azul arrange``.
  Generally, several files are created per workdir: one per active step.
  For pipelining, only the path to the last step (by default, ``adjusted``) is streamed out.
* ``azul arrange`` streams the path to the collage file toward ``open``.
