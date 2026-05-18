``azul roam``
=============

Overview
--------

Command ``azul roam`` consists in moving a so-called **viewport**
-- a rectangular region from which video frames are extracted --
over an input image.
The image and viewport can be seen as analogous to a scene and camera, respectively.

The viewport has a variable center, field of view and rotation angle.
The parameters at **key frames** are specified by the user.

The command supports the following frame capture modes:

Pan-and-zoom
   This is the simplest way of capturing frames, where the viewport supports only translation, scaling and rotation.
WCS transform
   In this mode, the input WCS parameters are used to warp the image
   as if the camera was not pointing perpendicularly to the image plane.
   This is more than an affine transform because distortion as computed by MER is taken into account.
Equirectangular
   This mode assumes that the input image is an equirectangular (plate-carrée) projection of the full sky,
   with RA from 180° on the left to -180° on the rigth
   and Dec from -90° at the bottom to 90° at the top.
Gaia Sky
   This special mode consists in capturing frames from a running `Gaia Sky <https://gaiasky.space/>`_ instance.
   No other input data (no image) is used.
   The Gaia Sky mode is provided for creating seamless transitions between planetarium and Euclid data.


.. plantuml::
   :align: center
   :max-width: 100%

   skinparam backgroundColor transparent

   file image {
   }

   object Subsample {
   }
   object Interpolate {
   --format
   --fps
   --start
   --stop
   }
   object Capture {
   --planar
   --wcs
   --equirectangular
   --gaiasky
   }

   file video {
   }

   image --> Subsample
   Subsample -> Interpolate
   Interpolate -> Capture
   Capture --> video


Input
-----

``azul roam`` takes as input a single image path,
given as a positional argument or through ``stdin``.

The key frames are specified through a so-called **sequence file**
passed to option ``--planar``, ``--wcs``, ``--equirectangular`` or ``--gaiasky``
depending on the wanted frame capture mode.


Output
------

The video produced by ``azul roam`` is a saved following a template given to option ``-o``.
Placeholders are:

================ ==================
Placeholder name Substitution value
================ ==================
``{workspace}``  Workspace path
``{image}``      Input image stem
``{sequence}``   Sequence file stem
================ ==================

Several video file formats are supported (see the help message for a complete list),
among which MKV (the default) features lossless compression, which is needed for further video compositing.


Image subsampling
-----------------

Except for Gaia Sky mode, in order to speed up computation and get rid of aliasing with small fields of view,
a multiresolution image pyramid is built.
Frames will be extracted from this image through geometric transformations, according to the capture mode.


Viewport parameters interpolation
---------------------------------

The main command line argument of ``azul roam`` is a so-called key frame sequence file (or sequence file in short).
It contains the specifications of key frames: time and viewport parameters.
Between key frames, the viewport geometry is sine-interpolated to ensure smooth transitions.
The path of the center can also be spline-interpolated to avoid unnatural-looking zigzag patterns.

TODO: sequence file format

Interpolation also depends on the following parameters:

``--format``
   The video format, given either as a ``<width>,<height>`` or as a standard "K"-format such as ``2K`` or ``4K``.
``--fps``
   The number of frames per second.
``--start`` and ``--stop``
   The 0-based indices of the first and last frames to be captured.

Frame capture
-------------

TODO
