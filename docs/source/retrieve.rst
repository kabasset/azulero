``azul retrieve``
=================

Overview
--------

VIS and NIR bands of the MER mosaics can be found and downloaded with ``azul retrieve``.
A variety of targets can be queried.
For each of the input target, an output workdir is created,
to which data files are then downloaded.

The diagram below illustrates the steps performed by ``azul retrieve``
to download data files for a single target.
Command line parameters, if any, are listed below the step name.

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
   -o
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

Data providers and setup
------------------------

Query and download steps rely on so-called **data providers**.

Several data providers are supported, namely:

* all of the ``astroquery.esa.euclid`` environments
  (e.g. ``pdr`` for Public Data Releases and ``idr`` for Internal Data Releases),
* Euclid's internal Distributed Storage System (DSS).

The provider name is passed to option ``--from`` and applies to all of the targets of the command line:

.. prompt:: bash

   azul retrieve NGC6505 270.93,67.05 102157949 --from pdr


.. note::

   The default value for this option can be overwritten by environment variable ``AZULRETRIEVE_FROM``
   (see :ref:`named_options` for more details),
   which is very convenient **for users without a Euclid account**
   (for example, on Linux, add the following to your ``.bashrc`` file)::

      export AZULRETRIEVE_FROM=pdr

.. warning::

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

TODO: Tiling file


Inputs
------

The command takes as input a list of so-called targets, which may be of different types:

* tile index,
* coordinates,
* named object.

Tiles are passed as integers.
Coordinates are passed using any format accepted by Astropy's ``SkyCoord``,
typically as ICRS comma-separated right ascension and declination.
Named objects are passed as strings, coordinates of which are looked up in the CDS name resolver.

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
Several tiles may cover a single target, such that several workdirs may be created for each of them.
Conversely, several targets may belong a same tile, in which case workdirs have a common parent tile folder.
At the time of writing, the above command creates the following workdirs:

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


Name resolution
---------------

In order for ``azul retrieve`` to download the tiles or cutouts containing a named object,
the coordinates of the latter are queried to the CDS.
If the name has to contain spaces or special characters, the name must be given between quotes.
In general, spaces can be omitted, though, such that the two following lines are equivalent:

.. prompt:: bash

   azul retrieve "NGC 6505"
   azul retrieve NGC6505


Query
-----

TODO --dsr, -n


Download
--------

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

TODO: -o, -f