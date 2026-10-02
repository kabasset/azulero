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
   They are case-insensitive such that ``dr1`` and ``DR1`` are the same.
   Special preset ``current`` lists all of the currently defined environment variables
   which start with the Azulero prefix (see :doc:`interfaces`).

If no value is given, the list of available presets is printed.


Outputs
-------

The output is a list of environment variables written as ``<name>=<value>``.
Generally, they should be written to some ``.env`` file, which is read by other commands (see :doc:`interfaces`).

Here is an example command aimed at later retrieving cutouts of radius 10 arcsec from DR1 data in ESA's Datalabs:

.. code-block:: console
   :emphasize-text: > >>

   $ azul env dr1 AZULRETRIEVE_RADIUS=10s datalabs > .env  # Create or overwrite .env
   $ azul env dr1 AZULRETRIEVE_RADIUS=10s datalabs >> .env  # Append to .env


Variable collection
-------------------

The different input arguments are processed in order as follows, starting from an empty environment:

* If there is an equal sign, append the environment variable to the environment;
* Otherwise, find the preset with given name and append all of its environment variables to the environment.

All variables which start with the Azulero prefix are then re-prefixed with the value of ``--prefix``.


On prefixes
-----------

Using different prefixes is a convenient way to work with a single ``.env`` file
and activate the various groups of variables defined in it by changing the Azulero prefix.

For example, let's create a ``.env`` file which stores some configuration for both Q1 and DR1 processing:

.. code-block:: console
   :emphasize-text: AZULQ1 AZULDR1

   $ export AZUL_LOG=DEBUG
   $ azul env --prefix AZULQ1 current q1 AZUL_WORKSPACE=./Q1 >> .env
   $ azul env --prefix AZULDR1 current dr1 AZUL_WORKSPACE=./DR1 >> .env

   $ AZULERO_PREFIX=AZULQ1 azul retrieve NGC6505 -r 1m | azul process
   $ AZULERO_PREFIX=AZULDR1 azul retrieve NGC6505 -r 1m | azul process

Note that ``AZUL_LOG`` is collected by preset ``current`` because it starts with ``AZUL``,
while it is rendered as both ``AZULQ1_LOG`` and ``AZULDR1_LOG`` in ``.env``.
Similarly, the workspaces are correctly rendered as ``AZULQ1_WORKSPACE=./Q1`` and ``AZULDR1_WORKSPACE=./DR1``.
