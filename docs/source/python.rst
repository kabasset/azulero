Python API
==========

Introduction
^^^^^^^^^^^^

In order to avoid generating useless files when working with data already in memory, a Python interface is published.
The package comes with a library, public interface of which is contained in module ``api``.
For example, assuming the photometric channels are NumPy arrays ``i, y, j h``, the RGB (or, rather, BGR image) is rendered as:

.. code-block:: python
   :emphasize-text: azulero api azul

   from azulero import api as azul

   iyjh = np.stack([i, y, j, h])
   bgr = azul.process_iyjh(iyjh)


API reference
^^^^^^^^^^^^^

.. automodule:: azulero.api
   :members:
