Data retrieval
==============

Introduction
------------

The input files of Azulero are individual MER mosaics, which can be downloaded with ``azul retrieve``.

Euclid data are found and downloaded with command ``azul retrieve``.
It takes as input a list of so-called targets, which may be of different types:

* tile,
* coordinates,
* named object.

Tiles are passed as integers.
Coordinates are passed as ICRS comma-separated right ascension and declination;
All formats accepted by Astropy's ``SkyCoord`` are valid.
Named objects are passed as strings.

For example, the following command would retrieve the tiles covering targets of each type:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949


Workspace and workdirs
----------------------

The files are downloaded into a dedicated workdir for each target, inside some parent workspace.
By default, the worspace is the current directory (``.``).
It can be configured with option ``--workspace``:

.. prompt:: bash

   azul --workspace /tmp retrieve NGC6505 270.93,67.05 102157949

Note that this is an option of ``azul`` and not ``azul retrieve``,
because it will be used by other ``azul`` commands.

The wokdirs are named after the targets, grouped by tile index.
Several tiles may cover a single target, such that several workdirs may be created for each of them.
At the time of writing, the above command creates the following workdirs::

   /tmp
   |
   ├── 101832848
   │   └── NGC6505
   |
   ├── 101832849
   │ └── NGC6505
   |
   ├── 101836362
   │   └── 270.93,67.05
   |
   ├── 102157949
   |
   ├── 102158889
   │   └── NGC6505
   |
   └── 102159776
       └── 270.93,67.05


Providers
---------

Several data providers are supported, namely
all of the ``astroquery.esa.euclid`` environments
(e.g. ``pdr`` for Public Data Releases and ``idr`` for Internal Data Releases),
as well as Euclid's internal Distributed Storage System (DSS).

The provider name is passed to option ``--from`` and applies to all targets of the command line:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949 --from pdr

The default value for this option can be overwritten by environment variable ``AZULRETRIEVE_FROM``
(see :ref:`named_options` for more details),
which is very convenient for users without a Euclid account::

   export AZULRETRIEVE_FROM=pdr

Non public data providers (all providers but ``pdr``) require authentication,
which is set up in the netrc configuration file (``~/.netrc`` on Unix, ``_netrc`` on Windows).

For accessing ``astroquery`` environments, a SAS account is needed:

.. code-block:: xml

   machine easidr.esac.esa.int
     login <login>
     password <password>

Similarly, for DSS data, an EAS account has to be configured:

.. code-block:: xml

   machine eas-dps-rest-ops.esac.esa.int
     login <login>
     password <password>
   machine euclidsoc.esac.esa.int
     login <login>
     password <password>

Cutouts
-------

When retrieving coordinates or named objects, a cone radius can be passed as option ``--radius``,
which triggers a cutout service and downloads only a square region around the target.
All formats handled by Astropy's ``Angle`` are accepted.

The radius applies to all coordinates and named objects of the command line,
but not to the tile targets.
Therefore, the following line:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949 --radius 1m

downloads 2' x 2' regions for NGC6505 and (270.93, 67.05), as well as the whole 102157949 tile.

.. warning:: As of today, provider ``dss`` does not support the cutout service.
