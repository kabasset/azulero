What's new
==========

Version 2.1
-----------

The main focus of this version is to make batch processing more flexible,
for example by retrieving cutouts of different sizes,
bypassing the download phase when working on the Datalabs,
or calling Azulero directly from Python (notebooks).
Additional upgrades include the revival of ``azul crop``
and the improvement of the background rendering with ``azul process``.

Below are a few more details; for more, see the :doc:`changes`.

``azul retrieve``
   * In a single command, multiple radii are supported for cutout retrieval.
   * On ESA Datalabs, no downloads or copies are performed with ``--data labs``.
   * Queries and downloads are retried on failure.

``azul process``
   * The sky background is now darker by default, and less dependent on the white point,
     which makes it more stable with ``-w 0``.
   * In incomplete tiles, the large empty regions are not inpainted anymore,
     which means the RAM usage is reasonable and the empty regions are rendered dark.
   * Files with one extension per band are accepted as targets.
   * A Python API is delivered.


Version 2.0
-----------

This version is an almost complete rewriting of Azulero.
We have reworked every aspect of the software
from the lowest level (pixel ordering, logging, code quality)
to the highest level (parametrization, documentation, workflow).
The result is a much cleaner and more extensible design, able to accommodate novel features more efficiently.
Speaking of which, the purpose of this release is mass production of images.
To this end, we introduce **cutout retrieval** and **pipelining**.
In turn, they enable faster and parallel processing, as well as streamlined production workflows.
In addition, Azulero 2.0 introduces new command :doc:`arrange` aimed at performing a very common post-processing stage:
making **collages** from collections of images.

Cutout retrieval
   Command :doc:`retrieve` can now download tile regions, which may save a significant amount of time and disk space.
   Typically, a 1' x 1' cutout is 1000x smaller and therefore 1000x faster to download and process than a WIDE tile.

Pipelining
   Pipelining is a new way of chaining operations with Azulero.
   Relying on the Unix or Windows pipe operator, it is now possible to execute the various image production stages
   (e.g. downloading, rendering and collage) in a single command line.

Collage
   New command :doc:`arrange` arranges input images into a grid.
   In combination with cutout retrieval, it offers a very convenient way to render images from catalogs.

All of these evolutions come with breaking changes, thus the major version number.
Here is an overview (for more details, see the :doc:`changes`):

Updated commands with breaking changes:

* :doc:`retrieve`
* :doc:`process`
* :doc:`roam`

New command:

* :doc:`arrange`

Deprecated commands:

* ``azul find`` (merged into :doc:`retrieve`)
* ``azul crop`` (to be updated later)
* ``azul assemble`` (superseded by :doc:`arrange`)
* ``azul overlay`` (to be updated later)
