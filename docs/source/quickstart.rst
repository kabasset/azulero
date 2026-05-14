Quick start
===========

How to read this documentation
------------------------------

Azulero is a command line toolbox made of several **commands**, e.g. ``azul retrieve`` or ``azul process``.
All of them follow a common interface on one hand, and have their own specificities on the other hand.

The shared interface concepts are described in :doc:`interfaces`
-- make sure to read this page first!
Then, each command has its dedicated documentation, named after itself!


.. note::
   
   If you are already familiar with Azulero v1, there is nothing more for you here:
   Jump to the :doc:`news` page!


Installation and setup
----------------------

In order to start working with Azulero, you will have to install it (see :doc:`install`)
and if you want to find and download Euclid data, you will need to set up ``azul retrieve`` (see :ref:`setup`).


Your first image
----------------

Because you may not want to read documentation now that everything was just setup,
we propose to create an image before (carefully) reading the next pages!

We will start by downloading some Euclid data around a colorful and large-enough-but-not-too-large galaxy:
`UGC 11169 <https://www.cosmos.esa.int/web/euclid/euclid-nearby-galaxies-collage>`_.
Go to your favorite directory and run:

.. prompt:: bash

   azul retrieve UGC11169 -r 30s | azul process -w 0

This will retrieve and process an area of 1' x 1' or roughly 600 x 600 pixels around the galaxy core.
Wait for a few seconds for the commands to complete...
At the end of the logs, you should see the path to which the glorious color image was written,
which you can already open and admire!
