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
   from azulero import api as azul

   iyjh = np.stack([i, y, j, h])
   bgr = azul.process_iyjh(iyjh)

For convenience, ``azul retrieve`` features have also been ported to the API, as class ``DataProvider``:

.. code-block:: python
   :emphasize-text: azulero api DataProvider query_coord_tiles query_tile_datafiles download_cutouts

   from astropy.coordinates import Angle, SkyCoord
   from pathlib import Path
   from azulero import api as azul

   coord = SkyCoord.from_name("NGC6505")
   radius = Angle("30s")
   dsr = "DR1_R1"

   provider = azul.DataProvider("IDR")
   tiles = provider.query_coord_tiles(coord, [dsr], ["WIDE"])
   datafiles = provider.query_tile_datafiles(tiles[0], dsr)
   provider.download_cutouts(datafiles, Path("/tmp"), coord, radius)


API reference
^^^^^^^^^^^^^

.. automodule:: azulero.api
   :members:
