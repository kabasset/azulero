``azul arrange``
================

Overview
--------

The command creates a collage image which contains all of the input images arranged into a grid,
possibly with spacing between images and around the collage.

.. plantuml::
   :align: center
   :max-width: 100%

   skinparam backgroundColor transparent

   file images {
   }

   object Initialize {
   -n
   --format
   --margin
   --gap
   --background
   }
   object Blit {
   }

   file collage {
   }

   images --> Initialize
   Initialize -> Blit
   Blit --> collage


Inputs
------

The command takes as input a list of images,
which do not need to have the same formats or shapes.


Output
------

The output is a path rendered from a template passed to ``-o`` as follows:

================ ==================
Placeholder name Substitution value
================ ==================
``{workspace}``  Workspace path
``{first}``      The stem of the first input file
``{sequence}``   The stem of the last input file
================ ==================


Canvas initialization
---------------------

The canvas is initialized with a format and color.
First, the width and height of the grid cells are computed
from the input image sizes and ``--format`` parameter.

TODO document ``--format``

Then, the number of rows and columns is computed according to ``-n``
which specifies the maximum number of columns.
If the parameter is not specified, then a single row will be generated.

Between rows and columns, a spacing is specified to option ``--gap``
either in pixels or in percentage of the maximum cell extent if suffixed with ``%``.
Around the whole collage, a margin can also be specified to ``--margin`` in pixels or cell extent percentage.

The initial color of the canvas is given to option ``--background``.
This impacts the color of the gap and margin pixels,
as well as regions around cells which accommodate small images (see next session).


Image blitting
--------------

Blitting is the process of copying the input images into the canvas grid cells
(for purists here, we do not use Boolean operators to copy images and should probably not use this term).
Images are centered in their cells and the blit region is the intersection between the cell and image footprints:

* Input images higher or wider than the cell are cropped;
* The background remains visible around images smaller than the cell along at least one axis.

Images are row-major ordered from left to right and from top to bottom,
such that the leftmost image of the second top row is indexed ``-n`` in the input list.
The last row may be incomplete.
For example, here is how 5 images would be ordered with ``-n 3``
(5-pixel margins are shown in blue and 2-pixel gaps in red):

.. table::
   :name: arrange-grid

   +---+---+---+
   | 0 | 1 | 2 |
   +---+---+---+
   | 3 | 4 |   |
   +---+---+---+

