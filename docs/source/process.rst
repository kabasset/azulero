``azul process``
================

Overview
--------

Command ``azul process`` generates a defect-inpainted color image of a tile or tile cutout
from input MER images generally retrieved with ``azul retrieve``.
It takes as input workdirs which each contain at least one such MER image per Euclid photometric band (I, Y, J, H),
and outputs one color rendering per workdir.
Intermediate files can be written, mostly for investigation.

.. |I_band| thumbnail:: _static/iyjh/VIS.png
   :group: iyjh
.. |Y_band| thumbnail:: _static/iyjh/NIR-Y.png
   :group: iyjh
.. |J_band| thumbnail:: _static/iyjh/NIR-J.png
   :group: iyjh
.. |H_band| thumbnail:: _static/iyjh/NIR-H.png
   :group: iyjh
.. |RGB_out| thumbnail:: _static/iyjh/RGB.png
   :group: iyjh

.. table::
   :class: subfigure
   :widths: 20 20 20 20 20

   +----------+----------+----------+----------+-----------+
   | |I_band| | |Y_band| | |J_band| | |H_band| | |RGB_out| |
   +----------+----------+----------+----------+-----------+
   | I band   | Y band   | J band   | H band   | Output    |
   +----------+----------+----------+----------+-----------+

The diagram below illustrates the various steps of the algorithm processing a single workdir.

.. plantuml::
   :align: center
   :max-width: 100%

   folder target {
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
   --overshoot
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

   target --> Stack
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

The command takes as input a list of targets, which can be workdirs (see :ref:`workspace`) or multi-extension FITS files.
Default option values are tailored for workdirs created with ``azul retrieve``.
For data obtained differently, here is how to configure Azulero:

* For each workdir, input files are discovered according to their names in the workdir and a glob pattern.
  The glob pattern is built from a template given to global option ``--input``, e.g. ``*{channel}*.fits``
  and a collection of four channel names given to ``--channels`` used to substitute placeholder ``{channel}``.
* For each FITS file, the extension must be named after global option ``--channels``.

For more details, see help messages of global options ``--workspace``, ``--input`` and ``--channels``:

.. code-block:: console
   :emphasize-text: -h

   $ azul -h


Outputs
-------

The script results in a 16-bit TIFF, 8-bit PNG or 8-bit compressed JPG
depending on the extension of the file name parameter (``-o``).

WCS parameters are written as follows:

* TIFF outputs contain WCS parameters as ``ImageDescription`` metadata,
  for compatibility with euniverse_;
* PNG and JPEG outputs are accompanied with YAML files containing WCS parameters,
  named after the image file with ``.wcs`` extension.

The value passed to ``-o`` is a template in which the placeholders are rendered as follows.

================ ==================
Placeholder name Substitution value
================ ==================
``{workspace}``  Workspace path
``{workdir}``    Workdir path relative to the workspace
``{n}``          0-based ``n``-th part of the workdir
``{n|default}``  ``n``-th part of the workdir if it exists, otherwise ``default``
``{step}``       Name of the current step output (see below)
================ ==================

Intermediate images are saved when the template contains ``{step}``.
The latter will be replaced with the name of the intermediate step as follows:

* ``mask`` -- The color-coded bad pixel map, where 0 means the pixel is good,
  and grey (resp. blue, green, red) means the I (resp. Y, J, H) channel is bad.
* ``blended`` -- The RGB image before color and curve adjustment.
* ``adjusted`` -- The RGB image after color and curve adjustment, if any.

For example, using the template ``{workspace}/{workdir}/{0}_{step}.tiff``,
the inpainting mask of target 102159776 will be saved as ``102159776_mask.tiff`` in the workdir.
If, instead, ``-o {0}.jpg`` is used, then the output will be a JPG file in the current directory
accompanied by a ``.wcs`` file, and no intermediate steps will be saved.

For each target, only the path to the final image (not to the intermediate files or WCS file) is streamed to ``stdout``.


Stacking
--------

If several images are provided for a given band, they are median-stacked.
No alignment is performed since we assume the images are already MER-aligned.


Inpainting
----------

Many defects are masked by MER without being "corrected",
because correction would be detrimental to science (hallucination, increased noise level, uncalibrated response).
Most of the so-called *bad pixels* are assigned value 0 in the mosaics.
Azulero inpaints pixels with a null value after stacking.

Some defects may remain when they are not null in the mosaic (which may happen for a variety of reasons).
Relying on bitmasks to detect them and decide on the inpainting technique would be nice, especially for VIS ghosts,
yet we did not find a satisfying selection method, which would work both for WIDE and DEEP tiles.
We keep this in mind for a future version...

.. note::

   In order to cope with incomplete tiles, which have a large empty region,
   connected components from the bad pixel mask which touch a corner of the image are not inpainted.


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
Default white balance was tuned empirically over hundreds of images in order to render bright objects white in average.

The conversion between input intensity :math:`f` and AB magnitude :math:`m_\mathrm{AB}` is given by:

.. math::

   m_\mathrm{AB} = 2.5 \log_{10}(f) + \mathrm{ZP}

with :math:`\mathrm{ZP}` the zero-point.


Stretching
----------

The dynamic range is asinh-scaled, which yields pleasing results for both low- and high-energy regions.
The function is linear-like for low values and log-like for high values.
Above all, the transform is color-invariant such that if you change the stretching parameters,
only the rendered object luminosity will change, not its hue.

Stretching is controlled by:

* the white point (``-w``), which is the magnitude rendered white in the output image;
* an offset (``-b``), which is the opposite of the black point;
* a stretching parameter (``-a``) which sets the transition point between linear-like scaling and log-like scaling.

All of them are expressed in AB magnitude, therefore a higher value corresponds to a lower intensity.

In general, only the white point has to be adjusted, especially for very bright sources.
Typically, the Cat's eye nebula is extremely bright and best rendered with a white point around 18.
Special value ``-w 0`` triggers data-driven tuning based on image statistics.
It generally gives good results, but using it will prevent stitching multiple images,
since they will be rendered with inconsistent stretching parameters.
If you wish to make automatic parameter tuning the default,
set the following environment variable:

.. code-block:: console
   :emphasize-text: AZULPROCESS_WHITE

   $ export AZULPROCESS_WHITE=0

To demonstrate the effect and sensitivity of ``-w`` and ``-a``,
below is a matrix of UGC 11116 renderings in which we varied the parameters around their default values.

.. |200-2575| thumbnail:: _static/matrix/20-25.75.png
   :group: matrix
.. |225-2575| thumbnail:: _static/matrix/22.5-25.75.png
   :group: matrix
.. |250-2575| thumbnail:: _static/matrix/25-25.75.png
   :group: matrix
.. |200-2700| thumbnail:: _static/matrix/20-27.png
   :group: matrix
.. |225-2700| thumbnail:: _static/matrix/22.5-27.png
   :group: matrix
.. |250-2700| thumbnail:: _static/matrix/25-27.png
   :group: matrix
.. |200-2825| thumbnail:: _static/matrix/20-28.25.png
   :group: matrix
.. |225-2825| thumbnail:: _static/matrix/22.5-28.25.png
   :group: matrix
.. |250-2825| thumbnail:: _static/matrix/25-28.25.png
   :group: matrix

.. table::
   :class: subfigure
   :widths: 10 30 30 30

   +-----------+------------+------------+------------+
   | a = 28.25 | |200-2825| | |225-2825| | |250-2825| |
   +-----------+------------+------------+------------+
   | a = 27.00 | |200-2700| | |225-2700| | |250-2700| |
   +-----------+------------+------------+------------+
   | a = 25.75 | |200-2575| | |225-2575| | |250-2575| |
   +-----------+------------+------------+------------+
   |           | w = 20.0   | w = 22.5   | w = 25.0   |
   +-----------+------------+------------+------------+

The effect of ``-w`` is obvious at the heart of the galaxy, which is completely burnt in the rightmost column.
Note how pushing ``-a`` deeper (top row) intensifies dimmer objects like background galaxies and the outer region of UGC 11116.
Beware that it also increases noise and may make the background grainy and unpleasant.
Azulero default values are carefully chosen to limit this phenomenon while keeping room for post-processing.

The negative overshoot parameter (``--overshoot``) controls how much negative values remain in the rendered image.
A value of 0 means that input null values are rendered as 0,
while a value of 1 means that the offset value is rendered as 0.
Higher overshoot values provide more degrees of freedom for post-processing,
while lower values result in deeper blacks, which is better for using the rendered image directly.


Blending
--------

.. plantuml::
   :align: center
   :max-width: 100%

   left to right direction

   card L #777
   card VIS
   card NIR
   card I
   card Y
   card J
   card H
   card B #007
   card G #070
   card R #700

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
a intermediate lightness map (L) is built from the VIS (I) intensity and average NIR intensity
(specifically, the median stacking of YJH).
Resolution in VIS is better than in NIR,
therefore it has higher weight in the output lightness.

The different weight parameters control the different blending contributions:
``--ib`` (resp. ``--yg``, ``--jr``, ``--nirl``) control the relative contribution
of I (resp. Y, J, NIR) to B (resp. G, R, L).
As default parameters, we have chosen to use only I to generate B, and to compress YJH into GR.
Other research groups made different choices
like skipping completely J for ERO images,
using I only for L and YJH for RGB in many articles,
or merging YJ into G and use only H for R in the eummy_ package.
The default parameters of Azulero were challenged on thousands of various objects and always gave pleasant results.
That being said, there is no good or bad approach and you can create your own palette by varying the blending parameters.


Adjustment
----------

Before combining the intermediate RGB and L channels,
hue is rotated (parameter ``--hue``) and saturation is boosted (``--saturation``).
The default hue rotation reduces artificial-looking greens,
while the default, very light saturation boost aims at highlighting dust lanes.

The intensity of each color channel is then adjusted using splines
similar to Photoshop and Gimp curves (``--curves``).
By default, mid-tone blue intensities are increased a bit, which makes outer regions of galaxies stand out
and gives a subtle blue shade to the background noise.

All adjustments can be disabled by setting:

.. code-block:: console
   :emphasize-text: --hue --saturation --curves

   --hue 0 --saturation 1 --curves ""


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

Scalability is roughly linear (except for the stacking and inpainting steps),
such that you should be able to interpolate the needs wrt. the input shape.
In order to lower the memory consumption, it is possible to crop the image with NumPy's syntax,
e.g. for some top-left region (:math:`x < 6000, y \geq \mathrm{height} - 4000`):

.. code-block:: console
   :emphasize-text: [ ] : ,

   $ azul process 102159776[-4000:,:6000]

Depending on your system, it may be necessary to add quotes:

.. code-block:: console
   :emphasize-text: "

   $ azul process "102159776[-4000:,:6000]"

For a more user-friendly way of cropping, see :doc:`crop`.

.. _eummy: https://github.com/schirmermischa/eummy
.. _euniverse: https://github.com/schirmermischa/euniverse