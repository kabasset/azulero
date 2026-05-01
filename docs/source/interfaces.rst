General interface design
========================

.. warning:: To be written

Introduction
------------

TODO

Commands
--------

TODO

..  _named_options:

Named options
-------------

Named options like ``--workspace`` are not forwarded through pipelines.
Typically, the following pipeline would break:

.. prompt:: bash

   azul --workspace /tmp retrieve NGC6505 | azul process

because ``azul process`` would use the default workspace (``.``)
instead of the custom workspace given to ``azul retrieve``.

Therefore, we have implemented an environment-level mechanism in order to avoid repeating them from command to command.
Each named option can be read from an environment variable named as follows:

.. code-block:: xml

   AZUL<COMMAND>_<OPTION>

where:

* ``<COMMAND>`` is the uppercase command name, if any, such as ``RETRIEVE`` or ``PROCESS``;
* ``<OPTION>`` is the uppercase long-from option name, such as ``FROM`` for ``--from``
  or ``WHITE`` for ``--white`` (but not ``W`` for ``-w``).

For example:

.. prompt:: bash

   export AZUL_LOG=DEBUG
   export AZULRETRIEVE_FROM=pdr
   export AZULRETRIEVE_RADIUS=1m

sets the log level to ``DEBUG`` for all commands,
and sets the data provider to ``pdr`` and crop radius to 1 arcmin for ``azul retrieve``.
These parameters are overloaded by command line arguments.

Within this context, the following lines are equivalent:

.. prompt:: bash

   azul retrieve NGC6505 UGC11116 | azul process
   azul --log DEBUG retrieve NGC6505 UGC11116 -r 1m --from pdr -f | azul --log DEBUG process

