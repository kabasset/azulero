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


Inpainting
----------

Different algorithms are used to inpaint VIS and NISP invalid pixels.
Specifically, color images and image stacks are inpainted with SciKit's biharmonic algorithm,
while grayscale images are inpainted with OpenCV's Navier-Stokes algorithm.
The former is very memory-greedy but renders much smoother large regions,
which often occur at the center of galaxies.
