``azul arrange``
================

Overview
--------

The command creates a collage image which contains all of the input images arranged into a grid,
possibly with spacing between images and around the collage.

.. plantuml::
   :align: center
   :max-width: 100%

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
``{last}``       The stem of the last input file
================ ==================


Canvas initialization
---------------------

A canvas (the background of the collage) is initialized with a format and color.
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

Blitting is the process of copying the input images onto the canvas grid cells
(for purists here, we do not use Boolean operators to copy images and should probably not use this term).
Images are centered in their cells and the blit region is the intersection between the cell and image footprints:

* Input images higher or wider than the cell are cropped;
* The background remains visible around images smaller than the cell along at least one axis.

Images are row-major ordered from left to right and from top to bottom,
such that the leftmost image of the second top row is indexed ``-n`` in the input list.
The last row may be incomplete.
For example, here is how 5 images would be ordered with ``-n 3``:

.. raw:: html

   <table style="width: 150px; margin-left: auto; margin-right: auto; text-align: center; border: 5px solid gray;">
   <tr>
   <td style="width: 50px; height: 50px; padding: 0; border: 2px solid gray">0</td>
   <td style="width: 50px; height: 50px; padding: 0; border: 2px solid gray">1</td>
   <td style="width: 50px; height: 50px; padding: 0; border: 2px solid gray">2</td>
   </tr>
   <tr>
   <td style="width: 50px; height: 50px; padding: 0; border: 2px solid gray">3</td>
   <td style="width: 50px; height: 50px; padding: 0; border: 2px solid gray">4</td>
   <td style="width: 50px; height: 50px; padding: 0; border: 2px solid gray; background: gray;"></td>
   </tr>
   </table>

For demonstration, we used 5-pixel margins and 2-pixel gaps with a gray background.
