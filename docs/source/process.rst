``azul process``
================

Overview
--------

Command ``azul process`` generates a defect-inpainted color image of a tile or tile cutout
from input MER images generally retrieved with ``azul retrieve``.
It takes as input workdirs which each contain at least one such MER image per Euclid photometric band (I, Y, J, H),
and outputs one color rendering per workdir.
Intermediate files can be written, mostly for debugging purposes.

The diagram below illustrates the various steps of the algorithm processing a single workdir.


.. plantuml::
   :align: center

   !theme mars
   skinparam backgroundColor #FAF3E8

   folder workdir {
   }
   object Stack {
   }
   object Inpaint {
   }
   object Sharpen {
   --fwhm
   --strength
   }
   object Equalize {
   --zero
   --scaling
   }
   object Stretch {
   -w
   -a
   -b
   }
   object Blend {
   --ib
   --yg
   --jr
   --nirl
   }
   object Adjust {
   --hue
   --saturation
   --curves
   }

   workdir --> Stack
   Stack -> Inpaint
   Inpaint -> Sharpen
   Sharpen -> Equalize
   Equalize -> Stretch
   Stretch -> Blend
   Blend -> Adjust

   file mask {
   }
   file blended {
   }
   file adjusted {
   }

   Inpaint --> mask
   Blend --> blended
   Adjust --> adjusted


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

* ``mask`` -- The color-coded bad pixel map, where 0 means the pixel is good,
  and grey (resp. blue, green, red) means the I (resp. Y, J, H) channel is bad.
* ``blended`` -- The RGB image before color and curve adjustment.
* ``adjusted`` -- The RGB image after color and curve adjustment, if any.

For example, using the template ``{workspace}/{workdir}/{target}_{tile}_{step}.tiff``,
the inpainting mask tile 102159776 will be saved as ``Tile_102159776_mask.tiff`` in the workdir.
If, instead, ``-o {tile}.jpg`` is used, then the output will be a single JPG file in the current directory
and no intermediate steps will be saved.


Stacking
--------

If several images are provided for a given band, they are median-stacked.
No alignment is performed, since we assume the images are already MER-aligned.


Inpainting
----------

Pixels with a null value after stacking are inpainted, but some defects may remain.
Relying on bitmasks to detect them and decide on the inpainting technique would be nice, especially for VIS ghosts,
yet we did not find a satisfying selection method, which would work both for WIDE and DEEP tiles.
We keep this in mind for a future version...


Sharpening
----------

Band-wise sharpening is performed according to the empirical PSF width, using unsharp mask filtering.
The sharpening strength can be adjusted with ``--strength``.
The PSF width parameter (``--fwhm``) should generally not be changed.


Equalization
------------

Bands are scaled according to their zero-point,
and white balance is controlled with a scaling parameter (``--scaling``).
The zero-point parameter (``--zero``) should generally not be changed.

The conversion between input intensity :math:`f` and AB magnitude :math:`m_\mathrm{AB}` is given by:

.. math::

   m_\mathrm{AB} = 2.5 \log_{10}(f) + \mathrm{ZP}

with ZP the zero-point.


Stretching
----------

The dynamic range is asinh-scaled, which yields pleasing results for both low- and high-energy regions.
The function is linear-like for low values and log-like for high values.
Scaling is controlled by:

* the white point (``-w``),
* an offset (``-b``), which is the opposite of the black point,
* a stretching parameter (``-a``) which sets the transition point between linear-like scaling and log-like scaling.

All of them are expressed in AB magnitude, therefore a higher value corresponds to a lower intensity.

In general, only the white point has to be adjusted, especially for very bright sources.
Typically, the Cat's eye nebula is best rendered with a white point around 18.
Special value ``-w 0`` triggers data-driven tuning based on image statistics.
It generally gives good results, but using it will prevent stitching multiple images,
since they will be rendered with inconsistent stretching parameters.


Blending
--------

.. uml::
   :align: center

   !theme mars
   skinparam backgroundColor #FAF3E8
   left to right direction

   card L #FFFFFF
   card VIS #FFFFFF
   card NIR #FFFFFF
   card I
   card Y
   card J
   card H
   card B #8888FF
   card G #88FF88
   card R #FF8888

   L <-- NIR : nirl
   L <-- VIS
   VIS <-- I
   NIR <-- Y
   NIR <-- J
   NIR <-- H

   I --> B : ib
   Y --> B
   Y --> G : yg
   J --> G
   J --> R : jr
   H --> R

The blending generates an RGB image from four input channels.
We decide to keep the wavelength ordering: I < Y < J < H.
Two adjacent input channels may contribute to an output channel, e.g. Y and J may contribute to G.
An input channel may contribute to two adjacent output channels, e.g. Y may contribute to B and G.

In order to maximize resolution while retaining very red objects,
a intermediate lightness map (L) is built from the VIS (I) intensity and average NISP intensity
(specifically, the median stacking of YJH).
Resolution in VIS is better than in NISP,
therefore it has higher weight in the output lightness.

The different weight parameters control the different blending contributions.
We have chosen to use only I to generate B, and to compress YJH into GR.
Other research groups made different choices
like skipping completely J for ERO images,
using I only for L and YJH for RGB in many articles,
or merging YJ into G and use only H for R in the Eummy package.
The default parameters of Azulero were challenged on thousands of various objects and always give pleasant results.
That being said, there is no good or bad approach and you can create your own palette by varying the blending parameters.


Adjustment
----------

Before combining the intermediate RGB and L channels,
hue is rotated (parameter ``--hue``) and saturation is boosted (``--saturation``).
The intensity of each color channel is then adjusted using splines
similar to Photoshop and Gimp curves (``--curves``).

All adjustments can be disabled by setting ``--hue 0 --saturation 1 --curves ""``.


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
