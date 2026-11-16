Quick start
===========

Installation
------------

Latest release
^^^^^^^^^^^^^^

Azulero is a Python package deployed to `PyPI <https://pypi.org/project/azulero/>`_.
The simplest way to install it is with ``pip``:

.. code-block:: console
   :emphasize-text: azulero

   $ pip install azulero

If you already have an old version installed, use:

.. code-block:: console
   :emphasize-text: --upgrade

   $ pip install --upgrade azulero


Development version
^^^^^^^^^^^^^^^^^^^

If you simply want to get the development version from time to time,
uninstall the current version and install from the sources:

.. code-block:: console
   :emphasize-text: uninstall

   $ pip uninstall --yes azulero
   $ pip install git+https://github.com/kabasset/azulero

If instead, you want to modify the sources or update very often,
better clone the repository locally:

.. code-block:: console
   
   $ git clone https://github.com/kabasset/azulero
   $ cd azulero
   $ uv run pytest
   $ pip install .

Azulero is packaged with `uv <https://docs.astral.sh/uv/>`_.
Hence, there is no need to install the package in order to execute the scripts.
Instead, from the clone directory, you can prepend commands with ``uv run``.
For example, to download a cutout without installing, launch:

.. code-block:: console
   :emphasize-text: uv run

   $ uv run azul retrieve NGC6505 -r 1m


.. _setup:

Setup
-----

.. note::

   Since version 2.2, accessing public data requires no configuration.
   You can skip this section if you do not intend to use private data!

Euclid Consortium members can access private data when authenticated.
Three authentication methods are provided, which will be described in the following subsections:

``.netrc`` file
   In personal environments, credentials can be stored once for all in the ``.netrc`` file.

Interactive authentication
   In shared environments, passwords should not be stored in any file.
   If only the user name is written in the ``.netrc`` file, an interactive mode is triggered
   and you will be prompted for your password.

Session authentication
   Special command ``azul env print-user`` aims at authenticating the user for an entire terminal session
   without having the password appear in any file or terminal history.
   The interactive mode will be prompted to feed a dedicated environment variable.


Setup wizard and ``.netrc`` file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Setup wizard
   :class: tip

   Since version 2.2, a setup wizard will guide you through the initial setup.
   It will perform the steps described here.
   You can either follow the instructions below or run the following command:

   .. code-block:: console
      :emphasize-text: --setup

      $ azul env --setup

Credentials can be stored in the ``.netrc`` configuration file
(``~/.netrc`` on Unix, ``%HOMEPATH%\.netrc`` on Windows) as follows:

* For internal SAS data, use your LDAP credentials:

  .. code-block::
     :emphasize-text: LDAP_login LDAP_password

     machine easidr.esac.esa.int
       login <LDAP_login>
       password <LDAP_password>

* For DSS data, use your archive credentials:

  .. code-block::
     :emphasize-text: EC_login EC_password

     machine eas-dps-rest-ops.esac.esa.int
       login <EC_login>
       password <EC_password>
     machine euclidsoc.esac.esa.int
       login <EC_login>
       password <EC_password>


.. _printuser:

Session authentication
^^^^^^^^^^^^^^^^^^^^^^

If you are working in a shared environment like ESA Datalabs,
you should not save secrets in a ``.netrc`` file or terminal history.
In this specific case, please start by exporting your credentials using ``azul env`` as follows:

.. code-block:: console
   :emphasize-text: export print-user

   # Unix
   $ export $(azul env print-user)

   # Windows
   $ for /f %%x in ('azul env print-user') do set "%%x"

Authentication will be forgotten when the session closes.


ESA Datalabs users
^^^^^^^^^^^^^^^^^^

MER datafiles are directly accessible from ESA Datalabs, such that no download is needed.
To enable this feature permanently in Datalabs, add the following line to the ``.bashrc`` file
(see :doc:`retrieve` for details):

.. code-block:: console
   :emphasize-text: labs

   $ export AZULRETRIEVE_DATA=labs


Your first image
----------------

Because you may not want to read documentation now that everything was just setup,
we propose to create an image before (carefully) reading the next pages!

We will start by downloading some Euclid data around a colorful and large-enough-but-not-too-large galaxy:
`UGC 11169 <https://www.cosmos.esa.int/web/euclid/euclid-nearby-galaxies-collage>`_.
Go to your favorite directory and run:

.. code-block:: console
   :emphasize-text: retrieve process

   $ azul retrieve UGC11169 -r 30s | azul process -w 0

This will retrieve and process an area of 1' x 1' or roughly 600 x 600 pixels around the galaxy core.
Wait for a few seconds for the commands to complete...
At the end of the logs, you should see the path to which the glorious color image was written,
which you can already open and admire!


How to read the documentation?
------------------------------

Azulero is a command line toolbox made of several **commands**, e.g. ``azul retrieve`` or ``azul process``.
All of them follow a common interface on one hand, and have their own specificities on the other hand.

The shared interface concepts are described in :doc:`interfaces`
-- make sure to read this page first!

Then, each command has its own documentation page named after itself, e.g. :doc:`retrieve` or :doc:`process`.
In these pages, commands are presented graphically, like:

.. plantuml::
   :align: center
   :max-width: 100%

   file input {
   }

   object Step1 {
   --param1
   }
   object Step2 {
   }
   object Step3 {
   --param2
   }

   file interm {
   }

   file output {
   }

   input --> Step1
   Step1 -> Step2
   Step2 -> Step3
   Step2 --> interm
   Step3 --> output

The diagram depicts the sequence of steps performed by the command.
If any, the command line options are listed for each step.
On top of the sequence are the inputs, and below the sequence are the (intermediate and final) outputs.

After this overview section, inputs and outputs are described.
Then, more details are given for each step and parameter.
Additional sections may dive deeper on a case-by-case basis.

Users of the :doc:`python` should still read the commands documentation:
this is where the algorithms and their parameters are described.
