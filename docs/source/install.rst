
Installation guide
==================

Latest release
--------------

Azulero is deployed to `PyPI <https://pypi.org/project/azulero/>`_.
The simplest way to install it is with ``pip``:

.. prompt:: bash

   pip install azulero

If you already have an old version installed, use:

.. prompt:: bash

   pip install --upgrade azulero


Development version
-------------------

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
It is not needed to install the package to execute the scripts.
For example, to download a cutout without installing, launch:

.. prompt:: bash

    uv run azul retrieve NGC6505 -r 1m
