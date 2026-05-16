``azul retrieve``
=================

Overview
--------

``azul retrieve`` finds and downloads Euclid MER data which contain specified **targets**,
such as coordinates or named astronomical objects.
The retrieved files are organized in directories we call **workdirs**.

As depicted below, ``azul retrieve`` consists of two main steps:

#. Querying the indices of the tiles which contain input targets;
#. Downloading the data files in full or in part.

.. plantuml::
   :align: center
   :max-width: 100%

   skinparam backgroundColor transparent

   card target {
   }

   object Query {
   --from
   --dsr
   -n
   }
   object Download {
   -q
   -r
   -f
   }

   folder workdir {
   }

   target --> Query
   Query -> Download
   Download --> workdir


Inputs
------

The command takes as input the list of targets, which may be of different types:

Tiles
   Integers are parsed as tile indices.
Coordinates
   If the target contains a comma, it is considered as RA/Dec coordinates
   in degrees, using ICRS reference frame.
Named objects
   Other types of input are parsed as object names.
   Their coordinates are looked up in the `CDS name resolver`_.

For example, the following command would retrieve the tiles covering targets of each type:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949

If the target *has to* contain spaces or special characters, the argument must be given between quotes.
In general, spaces can be omitted, though, such that the two following lines are equivalent:

.. prompt:: bash

   azul retrieve "NGC 6505"
   azul retrieve NGC6505

.. warning:: Currently, using spaces in target names may break :doc:`pipelines`.


..  _workspace:

Outputs
-------

The files are downloaded into a dedicated **workdir** for each target, inside some parent **workspace**.
By default, the workspace is the current directory (``.``).
It can be configured with global option ``--workspace``:

.. prompt:: bash

   azul --workspace /tmp retrieve NGC6505 270.93,67.05 102157949 PGC61356

By default, the workdirs are named after the targets, grouped by tile index.
At the time of writing, the above command creates the following workdirs inside workspace ``/tmp``:

.. plantuml::
   :max-width: 100%

   @startfiles
   /tmp/101832848/NGC6505/
   /tmp/101832849/NGC6505/
   /tmp/101836362/270.93,67.05/
   /tmp/101836362/PGC61356/
   /tmp/102157949/
   /tmp/102158889/NGC6505/
   /tmp/102159776/270.93,67.05/
   /tmp/102159776/PGC61356/
   @endfiles

Several tiles (101832848 and 101832849) cover a single target (NGC6505),
such that several workdirs are created for each of them.
Conversely, several targets (270.93,67.05 and PGC61356) belong a same tile (101836362),
in which case workdirs have a common parent tile folder.

The way the workspace is structured depends on the output template parameter ``-o``.
The template is rendered as follows:

================ ==================
Placeholder name Substitution value
================ ==================
``{workspace}``  Workspace path
``{tile}``       Resolved target tile index
``{target}``     Verbatim target argument in command line
================ ==================


Query
-----

The querying phase consists in finding the tile indices of the input coordinates and resolved objects,
as well as the names of the files to be downloaded.

This step relies on what we call a **data provider**, passed to option ``--from``
(or through environment variable ``AZULRETRIEVE_FROM``).
and applies to all of the targets of the command line:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949 --from pdr

There are several such providers, which store different sets of data:

``pdr`` (Public Data Releases)
   Contains all public data.
   This is the only provider which does not require authentication.
``idr`` (Internal Data Releases)
   Contains SAS data under embargo which will later be released publicly.
``otf`` (on-the-fly)
   Contains unreleased SAS data.
   It is updated from time to time between data releases.
``dss`` (Distributed Storage System)
   Contains everything!

.. warning:: Provider ``dss`` does not natively support named objects and coordinates retrieval.

   A `MER tiling file <https://gitlab.euclid-sgs.uk/sy-tools/ST_SMT_DATA/-/raw/DR1/data/DpdMerFinalCatalog.geojson?ref_type=heads>`_
   must be given to option ``--tiling``.
   This is a temporary workaround which we hope to improve in the next version.


Download
--------

TODO

When retrieving coordinates or named objects, a cone radius can be passed as option ``-r``,
which triggers a cutout service and downloads only a square region around the target.
All formats handled by Astropy's ``Angle`` are accepted.

The radius applies to all coordinates and named objects of the command line,
but not to the tile targets.
Therefore, the following line:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949 -r 1m

downloads 2' x 2' regions for NGC6505 and (270.93, 67.05), as well as the whole 102157949 tile.

.. warning:: Provider ``dss`` does not natively support the cutout service.

   A full tile will be downloaded and cut locally.
   Ensure that the target and tile directories as specified with option ``-o`` are distinct
   (this is the case with the default value).

By default, if a file to be downloaded already exists in the specified workdir, it is skipped.
This behavior can be changed by forcing downloads with flag ``-f``.
In this case, files which already exist will be overwritten.

TODO selective forcing


More on data providers
----------------------

What we call a data provider is in fact a couple of Euclid components:
a database and a data store.

Querying relies on a database for finding the tile indices and MER file names.
There are two such databases provided by the Euclid Archive System (EAS):

* the Science Archive Service (EAS-SAS or simply SAS);
* the Data Processing System (EAS-DPS or DPS).

The SAS offers the spatial query and cutout service but does not know of all of the internal data,
while the DPS does reference everything
but does not offer the spatial query (at least, not in a reasonable amount of time) or cutout service.

Once the file names have been resolved, the files are downloaded from a data store.
The DSS is the storage associated to the DPS.
The other providers are associated to the SAS.
Therefore, selecting provider DSS means accessing metadata from the DPS and data from the DSS.
Only the latter is specified to ``azul retrieve``, and the former is deduced
(same goes for the other data providers with the SAS).

TODO: DSS tile query and cutout retrieval

.. _CDS name resolver: https://cds.unistra.fr/cgi-bin/Sesame
