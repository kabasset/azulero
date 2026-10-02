``azul env``
============

Overview
--------

This simplistic command collects custom and predefined environment variables
in order to prepare subsequent Azulero runs.

.. plantuml::
   :align: center
   :max-width: 100%

   card variables {
   }
   object Collect {
   --prefix
   }
   card environment {
   }

   variables --> Collect
   Collect --> environment


Inputs
------

The command accepts two types of inputs:

Variables
   Environment variables are specified as ``<name>=<value>``, e.g. ``AZULPROCESS_WHITE=0``.
Preset names
   Presets are specified by their name, e.g. ``dr1``.
   Special preset ``current`` lists all of the currently defined environment variables
   which start with a given prefix (see below).

If no value is given, the list of available presets is printed.


Outputs
-------

The output is a list of environment variables written as ``<name>=<value>``.
Generally, they should be written to some ``.env`` file, which is read by other commands (see :doc:`interfaces`).

Here is an example command aimed at later retrieving cutouts of radius 10 arcsec from DR1 data in ESA's Datalabs:

.. code-block:: console
   :emphasize-text: > >>

   $ azul env dr1 RETRIEVE_RADIUS=10s datalabs > .env  # Write new .env file
   $ azul env dr1 RETRIEVE_RADIUS=10s datalabs >> .env  # Append to .env file


Variable collection
-------------------

The different input arguments are processed in order as follows, starting from an empty environment:

* If there is an equal sign, append the environment variable to the environment;
* Otherwise, find the preset with given name and append all of its environment variables to the environment.

All predefined variables are prefixed with the value of ``--prefix``,
which defaults to the value of environment variable ``AZULERO_PREFIX`` if defined or ``AZUL``.

Using different prefixes is a convenient way to work with a single ``.env`` file
and activate the various groups of variables defined in it by changing ``AZULERO_PREFIX``.
