What's new
==========

Version 2.0
-----------

This version is an almost complete rewriting of Azulero.
We have reworked every aspect of the software
from the lowest level (pixel ordering, logging, code quality)
to the highest level (parametrization, documentation, workflow).
The result is a much cleaner and more extensible design, able to accommodate novel features more efficiently.
Speaking of which, the purpose of this release is mass production of images.
To this end,we introduce **cutout retrieval** and **pipelining**.
In turn, they enable faster and parallel processing, as well as streamlined production workflows.
Last but not least, Azulero v2 introduces new command :doc:`arrange` aimed at performing a very common post-processing stage:
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
Here is an overview (for more details, see the change log):

Updated commands:

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
