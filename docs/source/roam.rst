Video generation
================

Purpose
-------

Synopsis
--------

.. code::

    ┌───────┐
    │ image │
    └─▼─────┘
    azul roam
    ┌─▼─────┐
    │ video │
    └───────┘


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
