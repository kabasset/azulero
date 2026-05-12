``azul roam``
=============

Overview
--------

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

If the path is not absolute, then it is assumed to be relative to the workspace.


Output
------

The video produced by ``azul roam`` is a saved following a template given to option ``-o``.
See the command line interface documentation below for more details.


Parameters
----------

The main option of ``azul roam`` is a so-called sequence-file
containing the specifications of key frames: time and viewport parameters.


Command line interface
----------------------

.. argparse::
   :module: azulero.client
   :func: add_parser
   :path: roam
