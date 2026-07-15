Developer notes
===============

Image storage
-------------

Color images are stored as ``ndarray``'s following most OpenCV conventions:

* Axes are ordered as height, width, depth;
* Channels are ordered as BGRA;
* However, **contrary to OpenCV, the y-axis points upward** for compatibility with WCS.

Specifically, this impacts IOs, since non-FITS supported formats are stored from top to bottom.
Therefore, image IOs should always be performed with the ``azulero.image.io`` module.

Grayscale image stacks, such as the IYJH stack, use the first axis as an image index.

We use the word *shape* following NumPy's definition, while *format* is always the 2-element tuple of width and then height.


Inpainting
----------

Different algorithms are used to inpaint VIS and NISP invalid pixels.
Specifically, color images and image stacks are inpainted with SciKit's biharmonic algorithm,
while grayscale images are inpainted with OpenCV's Navier-Stokes algorithm.
The former is very memory-greedy but renders much smoother large regions,
which often occur at the center of galaxies.


Sharpening
----------

By default, we rely on MER's PSF estimates, which are a tad wider than VIS' and NIR's estimates,
in order to keep overshooting under control.


DPS tile lookup
---------------

The DPS does not offer fast-enough spatial queries to find the tiles in which a target lies.
Therefore, we used to rely on SMT's Geojson tiling.
In order to simplify the workflow by not requiring users to download and update the tiling themselves,
we have implemented an optimized mechanism for spatial queries:

1. Query the ``DpdMerMosaics`` with a central declination (attribute ``CRVAL2``) between two bounds
   computed from the target declination and some margin (the maximum half height of a tile).
2. Perform the spatial query locally, using this subset of tiles, like we used to do with the Geojson tiling.

Other optimizations could be implemented, like bounds on the right ascension, but that would be more tricky to compute
while accounting for poles and anti-meridian discontinuities.


DPS cutout service
------------------

At the moment, there is no cutout service in the DPS.
Therefore, we perform the cutout locally after downloading the full tile.
This assumes the ``-o`` parameter specifies different tile and target workdirs,
otherwise the tile will be overwritten by the cutout,
which may result in undefined behavior for subsequent retrievals.


Sequence file
-------------

``azul roam``'s sequence file is quite rich already, which may make it hard to read.
In order to simplify reading, we chose to make everything explicit, i.e. there is no default value or unit.
A data model would be welcome...
