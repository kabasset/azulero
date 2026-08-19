Python API
==========

Introduction
^^^^^^^^^^^^

In order to avoid generating useless files when working with data already in memory, a Python interface is published.
The package comes with a library, public interface of which is contained in module ``api``.
For example, assuming the photometric channels are NumPy arrays ``i, y, j h``, the RGB (or, rather, BGR image) is rendered as:

.. code-block:: python
   :emphasize-text: azulero api process_iyjh

   import numpy as np
   import azulero.api as azul

   iyjh = np.stack([i, y, j, h])
   bgr = azul.process_iyjh(iyjh)

.. admonition:: Image layout
   :class: note

   Grayscale image axes are:

   0. Y-axis from bottom to top,
   1. X-axis from left to right.

   In addition, color images have a third axis:

   2. color axis ordered as Blue, Green, Red.

For convenience, ``azul retrieve`` features have also been ported to the API, as class ``DataProvider``
(argument ``data="labs"`` triggers Datalabs retrieval mode, see :doc:`retrieve`):

.. code-block:: python
   :emphasize-text: azulero api DataProvider query_coord_tiles query_tile_datafiles download_cutouts

   from astropy.coordinates import Angle, SkyCoord
   from pathlib import Path
   import azulero.api as azul

   coord = SkyCoord.from_name("NGC6505")
   radius = Angle("30s")
   dsr = "Q1_R1"

   provider = azul.DataProvider("PDR", data="labs")
   tiles = provider.query_coord_tiles(coord, [dsr], ["WIDE"])
   datafiles = provider.query_tile_datafiles(tiles[0], dsr)
   provider.download_cutouts(datafiles, Path("workdir"), coord, radius)


API reference
^^^^^^^^^^^^^

.. automodule:: azulero.api
   :members:
