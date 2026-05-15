Quick start
===========

Installation
------------

Latest release
^^^^^^^^^^^^^^

Azulero is a Python package deployed to `PyPI <https://pypi.org/project/azulero/>`_.
The simplest way to install it is with ``pip``:

.. prompt:: bash

   pip install azulero

If you already have an old version installed, use:

.. prompt:: bash

   pip install --upgrade azulero


Development version
^^^^^^^^^^^^^^^^^^^

If you simply want to get the development version from time to time, use:

.. prompt:: bash

   pip install git+https://github.com/kabasset/azulero

If instead, you want to modify the sources or update very often,
better clone the repository locally:

.. prompt:: bash

   git clone https://github.com/kabasset/azulero
   cd azulero
   pip install .

Azulero is packaged with `uv <https://docs.astral.sh/uv/>`_.
Hence, there is no need to install the package in order to execute the scripts.
Instead, from the clone directory, you can prepend commands with ``uv run``.
For example, to download a cutout without installing, launch:

.. prompt:: bash

    uv run azul retrieve NGC6505 -r 1m


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


How to read the documentation
-----------------------------

Azulero is a command line toolbox made of several **commands**, e.g. ``azul retrieve`` or ``azul process``.
All of them follow a common interface on one hand, and have their own specificities on the other hand.

The shared interface concepts are described in :doc:`interfaces`
-- make sure to read this page first!
Then, each command has its own documentation page, named after itself!
