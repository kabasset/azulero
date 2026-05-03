What's new
==========

Version 2
---------

Azulero v2 is a major update wrt. v1.

First, it introduces two main features: cutout retrieval and pipelining.

* Cutout retrieval enables the download of tile regions, which may save a significant amount of time.
  Typically, a 1' x 1' cutout is 1000x smaller and therefore 1000x faster to download and process than a WIDE tile.
* Pipelining is a new way of chaining operations with Azulero.
  Relying on the Unix or Windows pipe operator, it is now possible to execute the various image production steps
  (e.g., downloading, rendering and collage) in a single command line.

In terms of breaking changes, many commands were deprecated, generally merged with other commands.
The only remaining commands from v1 are: ``retrieve``, ``process`` and ``roam``.
Former command ``find`` has been merged into ``retrieve`` and ``process``.
New command ``arrange`` superseeds the former experimental command ``assemble``.
Finally, ``crop`` is deprecated.
