``azul retrieve``
=================

Overview
--------

``azul retrieve`` finds and downloads Euclid MER data which contain specified **targets**,
such as coordinates or named astronomical objects.
The retrieved files are organized in directories we call **workdirs**.

The atomic MER data footprint is a **tile**
and all MER products over a tile (images, masks, catalogs) are properly aligned.
Tiles are assigned a unique **tile index**.
There are two main types of tiles: DEEP and WIDE.
DEEP tiles quite small (17' x 17' in the sky and roughly 10k x 10k pixels in images)
but made of several Euclid observations already stacked by MER.
Stacking makes fainter objects visible and lowers the noise level.
WIDE tiles are comparatively larger (32' x 32', 20k x 20k pixels) and not MER-stacked.
When there are several observations over a single WIDE tile,
``azul process`` stacks them itself.

As depicted below, ``azul retrieve`` constists of two main steps:

1. Querying the indices of the tiles which contain input targets;
1. Downloading the data files in full or in part.

.. plantuml::
   :align: center
   :max-width: 100%

   skinparam backgroundColor transparent

   card target {
   }

   object Resolve {
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

   target --> Resolve
   Resolve -> Query
   Query -> Download
   Download --> workdir


.. _setup:

Setup
-----

For Euclid members
^^^^^^^^^^^^^^^^^^

Accessing public data require no configuration.

Internal data retrieval requires authentication,
which is set up in the netrc configuration file (``~/.netrc`` on Unix, ``%HOMEPATH%\_netrc`` on Windows) as follows:

* For internal SAS data:

   .. code-block:: xml

      machine easidr.esac.esa.int
      login <login>
      password <password>

* For DSS data:

   .. code-block:: xml

      machine eas-dps-rest-ops.esac.esa.int
      login <login>
      password <password>
      machine euclidsoc.esac.esa.int
      login <login>
      password <password>

TODO: Tiling file for DSS


For other users
^^^^^^^^^^^^^^^

Because you will retrieve only public data,
you can setup your environment to always restrict queries to the PDR provider.
To do so, simply set the environment variable ``AZULRETRIEVE_FROM`` to ``pdr``
(read the remaining of this page and see :ref:`named_options` to know why).
Typically, Bash users may add the following to the ``.bashrc`` file::

   export AZULRETRIEVE_FROM=pdr

No other configuration is needed for public data.


Inputs
------

The command takes as input a list of so-called targets, which may be of different types:

* tile index,
* coordinates,
* named object.

Tiles are passed as integers.
Coordinates are passed using any format accepted by Astropy's ``SkyCoord``,
typically as ICRS comma-separated right ascension and declination.
Named objects are passed as strings,
coordinates of which are looked up in the `CDS name resolver <https://cds.unistra.fr/cgi-bin/Sesame>`_.

For example, the following command would retrieve the tiles covering targets of each type:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949


..  _workspace:

Outputs
-------

The files are downloaded into a dedicated **workdir** for each target, inside some parent **workspace**.
By default, the workspace is the current directory (``.``).
It can be configured with global option ``--workspace``:

.. prompt:: bash

   azul --workspace /tmp retrieve NGC6505 270.93,67.05 102157949 PGC61356

The workdirs are named after the targets, grouped by tile index.
Several tiles (e.g. 101832848 and 101832849) may cover a single target (NGC6505),
such that several workdirs may be created for each of them.
Conversely, several targets (270.93,67.05 and PGC61356) may belong a same tile (101836362),
in which case workdirs have a common parent tile folder.
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

In this 

The way the workspace is structured depends on the output template parameter ``-o``.

TODO

Name resolution
---------------

In order for ``azul retrieve`` to download data files containing a named object,
the coordinates of the latter are queried to the CDS name resolver.

If the name has to contain spaces or special characters, the argument must be given between quotes.
In general, spaces can be omitted, though, such that the two following lines are equivalent:

.. prompt:: bash

   azul retrieve "NGC 6505"
   azul retrieve NGC6505


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

* ``pdr``, for Public Data Releases, contains all public data;
* ``idr``, for Internal Data Releases, contains SAS data under embargo which will later be released as a PDR;
* ``otf``, for on-the-fly data, contains unreleased SAS data; it is updated from time to time between data releases;
* ``dss``, for Distributed Storage System, contains all data.


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

.. warning:: As of today, provider ``dss`` does not support the cutout service.

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
