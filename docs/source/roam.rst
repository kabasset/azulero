``azul roam``
=============

Overview
--------

Command ``azul roam`` consists in moving a so-called **viewport**
-- a region from which video frames are extracted --
over an input image.
The image and viewport can be seen as analogous to a scene and camera, respectively.

The viewport has a variable center, field of view and rotation angle around the line of sight.
The parameters at **key frames** are specified by the user.

The command supports the following frame capture modes:

Pan-and-zoom
   This is the simplest way of capturing frames, where the viewport supports only translation, scaling and rotation.
WCS transform (experimental)
   In this mode, the input WCS parameters are used to warp the image
   as if the camera was not pointing perpendicularly to the image plane.
   This is more than an affine transform because distortion as computed by MER is taken into account.
Equirectangular
   This mode assumes that the input image is an equirectangular (plate-carrée) projection of the full sky,
   with RA from 180° on the left to -180° on the right
   and Dec from -90° at the bottom to 90° at the top.
Gaia Sky
   This special mode consists in capturing frames from a running `Gaia Sky <https://gaiasky.space/>`_ instance.
   No other input data (no image) is used.
   The Gaia Sky mode is provided for creating seamless transitions between planetarium and Euclid data.


.. plantuml::
   :align: center
   :max-width: 100%

   file image {
   }

   object Interpolate {
   --format
   --fps
   --start
   --stop
   }
   object Capture {
   --ortho
   --wcs
   --equi
   --gaiasky
   }

   file video {
   }

   image --> Interpolate
   Interpolate -> Capture
   Capture --> video


Input
-----

In this version, ``azul roam`` takes as input a single image path,
given as a positional argument or through ``stdin``.

The key frames are specified through a so-called **sequence file**
passed to option ``--ortho``, ``--wcs``, ``--equi`` or ``--gaiasky``
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

Several video file formats are supported (see the help message for a complete list: ``azul roam -h``),
among which MKV (the default) features lossless compression, which is needed for further video compositing.


Viewport parameters interpolation
---------------------------------

The main command line argument of ``azul roam`` is a so-called **sequence file** (see last section).
It contains the specifications of **key frames**: time and viewport parameters.
Between key frames, the viewport geometry is sine-interpolated to ensure smooth transitions.
The path of the center can also be spline-interpolated using additional **control points**
in order to avoid unnatural-looking zigzag patterns.

Interpolation also depends on the following parameters:

``--format``
   The video format, given either as ``<width>,<height>`` or as a standard "K"-format such as ``2K`` or ``4K``.
``--fps``
   The number of frames per second.
``--start`` and ``--stop``
   The 0-based indices of the first and last frames to be captured.


Frame capture
-------------

Frame capture is the operation of determining the viewport pixel intensities from the input image.
To this end, we build the mathematical mapping between image and viewport positions according to the capture mode.

In general, the positions in the image are not integral and interpolation is needed.
As a tradeoff between speed and output quality, we use bicubic interpolants.

With ``--ortho``, a multiresolution pyramid is first computed for speed and antialiasing.
We plan to expand this to the other capture modes.


Sequence file
-------------

The configuration file contains a list of key frames with associated times,
as well as intermediate control points for smoothing trajectories.
Four variables are specified per key frame:

Time
   The time is specified either in seconds or in number of frames.
Center
   The center is specified either in sky coordinates, pixel coordinates or percentage of the image extents.
Field of view
   The viewport size is computed either from a solid angle,
   from a scale relative to the image pixel size, or relatively to the image extents.
Orientation
   The viewport orientation is a rotation angle around the line of sight specified clockwise in degrees or radians.

For each key frame but the first one, omitted parameters are copied from the previous key frame.
The sequence file is in YAML format, which is very compact but requires space discipline!
A typical key frame specification looks like this:

.. code-block:: yaml
   :emphasize-text: t c z r

   - t: +10s
     c: UGC 11116
     z: 80%
     r: 15°


Time
^^^^

The name of the key frame time parameter in the sequence file is ``t``.
It is specified in seconds with suffix ``s`` or number of frames with suffix ``f``.
Prefix ``+`` indicates a duration from previous key frame instead of a time point, e.g.:
``t: 1s`` means key frame at 1 second, ``t: +24f`` means 24 frames after the previous key frame.

The time of the first frame must be ``0s`` or ``0f``.


Center
^^^^^^

The viewport center is given with key ``c``.
Both image and sky coordinates are supported:

Image coordinates
   Suffix ``px`` indicates absolute image coordinates, while suffix ``%`` indicates percentage relative to the image width or height.
   Negative values are interpreted as backward coordinates, i.e. from the right and bottom.
   Typically, the viewport is centered with ``x: 50%, 50%``.
Sky coordinates
   Other formats of comma-separated pairs indicates RA/dec coordinates in ICRS frame.
Named object
   Similarly to :doc:`retrieve`, ``azul roam`` supports object names as sky coordinates.


Field of view
^^^^^^^^^^^^^

The viewport size is specified either as a scale factor or horizontal field of view, with key ``z``:

* When suffixed with ``%``, the parameter is interpreted as relative to the pixel size,
  such that ``z: 100%`` (resp. ``z: 50%``) means that one pixel in the output frame
  corresponds to one pixel (resp. two pixels) in the input image.
* When suffixed with ``w`` (resp. ``h``), the parameter value is a factor wrt. the image width (resp. height).
  Typically, a full-width viewport is specified as ``z: 1w`` and a full-height viewport is specified as ``z: 1h``.
* Angular quantities (e.g. suffixed with ``°``) indicate a horizontal field of view as a solid angle.

.. warning:: In pan-and-zoom mode, zoom levels higher than 100% are not supported.

   In Gaia Sky mode, fields of view smaller than 1° are not supported.


Orientation
^^^^^^^^^^^

Viewport orientation is the rotation angle around the line of sight, aka. roll angle.
The angular parameter has key ``r`` and can be given in radians with suffix ``pi``,
in addition to degrees (``d`` or ``°``), minutes (``m`` or ``'``) and seconds (``s`` or ``"``).
Its value is arbitrary to allow for multi-turns videos.
Typically, with ``r: 0pi`` in a key frame and ``r: 4pi`` in the next one, the viewport would perform two full turns.
Positive values mean clockwise rotation of the viewport, i.e. counterclockwise rotation of the image.


Elision
^^^^^^^

While all parameters can be omitted to denote no change from the previous frame,
field of view and orientation parameters support key frame elision, with the ellipsis syntax: ``...``.
In this case, for the eluded parameter, it is like the key frame did not exist.
This means the interpolation runs from the frame immediately before ellipsis until that immediately after ellipsis.
Several successive key frames can be eluded, as demonstrated in the example below.


Control points
^^^^^^^^^^^^^^

It is possible to make the center trajectory smooth instead of piecewise linear, by defining intermediate **control points** (spline knots),
which are positions the center must pass through between key frames.
They are specified by providing ``c`` only (no time or any other parameter has to be specified).
The following example is a ten-second circular trajectory with three intermediate knots:

.. code-block:: yaml
   :emphasize-text: t c z r

   - t: 0s
     c: 70%, 50%
     z: 100%
     r: 0°

   - c: 50%, 70%

   - c: 30%, 50%

   - c: 50%, 30%

   - t: 10s
     c: 70%, 50%


Example
-------

Consider the following sequence:

.. code-block:: yaml
   :emphasize-text: t c z r

   - t: 0s
     c: 50%, 50%
     z: 1h
     r: 0°

   - t: +1s
     r: ...

   - t: +10s
     c: 87%, 57%
     z: 0.2w
     r: ...

   - t: +5s
     r: ...

   - t: +10s
     c: 60%, 72%
     z: 100%
     r: ...

   - t: +5s
     r: -90°

   - t: +5s
     c: 50%, 50%
     z: 1h

   - t: +1s

It consists in eight key frames:

#. The video starts with a full-height, centered and horizontal viewport.
#. For one second, there is only a viewport rotation
   -- which will run continuously until the sixth key frame to reach 90° clockwise rotation of the image.
#. Then, in ten seconds, the viewport moves to position (87%, 57%) relative to the image extents,
   and we zoom until we the viewport width reaches 20% of the image width.
#. For the next five seconds, only the orientation continues to evolve.
#. For ten seconds, we pan to position (60%, 72%) and zoom to 100% pixel size.
#. Five seconds later, rotation stops.
#. In the next five seconds, we go back to the center of the image and zoom out to reach full image height again.
#. The video finally stays still for one second.
