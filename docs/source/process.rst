Image processing
================

Basics
------

Command ``azul process`` generates a defect-inpainted color image of a tile from input MER data retrieved with ``azul retrieve``.

.. mermaid::

    ---
    config:
    sankey:
        showValues: false
    ---
    sankey-beta

    NIR median,L,20
    I,L,180
    I,B,50
    Y,G,30
    Y,B,50
    H,R,10
    J,G,70
    J,R,90

We want to output an RGB image from four input channels: one VIS (I) and three NIR bands (Y, J, H).
We decide to keep the wavelength ordering: I < Y < J < H.
Two adjacent input channels may contribute to an output channel, e.g. Y and J may contribute to G.
An input channel may contribute to two adjacent output channels, e.g. Y may contribute to B and G.
Resolution in I is better than in other channels,
therefore it has higher weight in the output intensity (more precisely, lightness).
Different weight parameters control the different contributions.

The dynamic range is asinh-scaled, which yields pleasing results for both low- and high-energy regions.
The function is linear-like for low values and log-like for high values.
Scaling is controlled by two bounds -- black and white points -- and a stretching parameter which sets the transition point between linear-like scaling and log-like scaling.
They are expressed in AB magnitude, such that a higher value corresponds to a lower intensity.

Pixels with a null value are inpainted, but many defects remain.
Relying on bitmasks to detect them and decide on the inpainting technique would be better, especially for VIS ghosts, yet I did not find a satisfying selection method, which would work both for WIDE and DEEP tiles...


Algorithm
---------

The script proceeds as follows:

* Inpaint bad pixels, i.e. the ones with value 0.
* Sharpen each channel with an unsharp masking filter of given full-width at half maximum (``--fwhm``) and strength (``--shapen``);
  This step is disabled if the strength is 0.
* Scale each channel according to its zero point (``--zero``) and gain parameter (``--scaling``).
* Stretch the dynamic range with asinh function, using white point (``-w``),
  offset parameter (opposite of black point, ``-b``), and stretch parameter (``-a``) as AB magnitudes.
* Blend IYJH channels into RGB and lightness (L) channels
  according to the various flux parameters (``--ib``, ``--yg``, ``--jr``, ``--nirl``).
* Shift hue (``--hue``) and boost color saturation (``--saturation``).
* Adjust the colorwise response curves by specifying interpolating spline knots (``--curves``).


Inputs
------

Input files are discovered according to their names in the workdir (see :ref:`workspace`) and a glob pattern.
For more details, see help messages of options ``--workspace`` and ``--input`` with ``azul -h``.
When several files are given for a single channel, they are stacked as the median image.


Outputs
-------

The script results in a 32-bit FITS, 16-bit TIFF, 8-bit PNG or 8-bit compressed JPG
depending on the extension of the file name parameter (``-o``).
FITS outputs contain WCS parameters.
The value passed to ``-o`` is a template in which the placeholders are rendered as follows.

================ ==================
Placeholder name Substitution value
================ ==================
``{workspace}``  Workspace path
``{workdir}``    Workdir path relative to the workspace
``{tile}``       First part of the workdir
``{target}``     Last part of the workdir if it has several parts, otherwise ``Tile``
``{step}``       Name of the current step output (see below)
================ ==================

Intermediate images are saved when the template contains ``{step}``.
The latter will be replaced with the name of the intermediate step as follows:

* ``wcs`` -- The WCS parameters as a YAML map.
* ``mask`` -- The color-coded bad pixel map, where 0 means the pixel is good,
  and grey (resp. blue, green, red) means the I (resp. Y, J, H) channel is bad.
* ``blended`` -- The RGB image before color and curve adjustment.
* ``adjusted`` -- The RGB image after color and curve adjustment, if any.

When they are not images, like for WCS parameters saved as a YAML map, the extension is changed.

For example, using the default template ``{workspace}/{workdir}/{target}_{tile}_{step}.tiff``,
the WCS parameters of tile 102159776 will be saved as ``Tile_102159776_wcs.yaml`` in the workdir.
If, instead, ``-o {tile}.jpg`` is used, then the output will be a single JPG file in the current directory
and no intermediate steps will be saved.


Resources and cropping
----------------------

In its current version, the script may be very memory-greedy for full tiles.
Below is a typical profiling for DEEP and WIDE tiles, including elapsed time and peak RAM usage for each step.
Theses numbers are logged step-by-step during the execution of ``azul process``.
Walltime will depend on the CPU while RAM usage should be stable across architectures.

========== ============ ============
Step       10k x 10k px 20k x 20k px
========== ============ ============
Reading     10 s,  3 GB  10 s,  6 GB
Inpainting  25 s,  6 GB 110 s, 21 GB
Sharpening   5 s,  3 GB  70 s, 12 GB
Stretching   5 s,  2 GB  25 s,  8 GB
Blending    20 s,  6 GB  70 s, 22 GB
Adjustment  10 s,  4 GB  25 s, 12 GB

OVERALL     75 s,  6 GB 310 s, 22 GB
========== ============ ============

Scalability is roughly linear, such that you should be able to interpolate the needs wrt. the input shape.
In order to lower the memory consumption, it is possible to crop the image with numpy's syntax,
e.g. for the top-left quarter (x < 5000, y >= 5000):

.. prompt:: bash

   azul process 102159776[5000:,:5000]

Depending on your system, it may be necessary to add quotes:

.. prompt:: bash

   azul process "102159776[5000:,:5000]"
