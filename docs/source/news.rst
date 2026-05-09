What's new
==========

Version 2
---------

This version is an almost complete rewriting of Azulero.
We have reworked every aspect of the software
from the lowest level (pixel ordering, logging, code quality)
to the highest level (parametrization, documentation, workflow).
The result is a much cleaner and more extensible design,
able to accommodate novel features more efficiently.
Speaking of which, the raison-d'être of this release is mass production of images.
To this end,we introduce **cutout retrieval** and **pipelining**.
In turn, they enable faster and parallel processing,
as well as streamlined production workflows.

* **Cutout retrieval** enables the download of tile regions, which may save a significant amount of time.
  Typically, a 1' x 1' cutout is 1000x smaller and therefore 1000x faster to download and process than a WIDE tile.
* **Pipelining** is a new way of chaining operations with Azulero.
  Relying on the Unix or Windows pipe operator, it is now possible to execute the various image production steps
  (e.g. downloading, rendering and collage) in a single command line.

All of these evolutions come with a few breaking changes.
Many commands were deprecated -- generally merged with other commands.
The only remaining commands from v1 are: ``retrieve``, ``process`` and ``roam``.
Former command ``find`` has been merged into ``retrieve`` and ``process``.
New command ``arrange`` supersedes the former experimental command ``assemble``.
Finally, ``crop`` is deprecated.
