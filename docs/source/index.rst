Azulero
=======

.. toctree::
   :maxdepth: 1
   :hidden:

   primer
   news
   quickstart
   interfaces
   retrieve
   process
   arrange
   roam
   pipelines


Bring colors to Euclid tiles!
-----------------------------

Azulero is a toolbox for producing stunning color Euclid images.

It cleans and enhances MER data and combines the four Euclid photometric channels (I, Y, J, H) into an sRGB image.
Input data are retrieved from public or private archives, and post-processing commands produce mesmerizing collages and flowing videos.

Azulero is now compatible with Unix and Windows pipelines, which makes batch processing simple,
including with parallelization (see :doc:`pipelines`).
The image below is the unedited output of:

.. prompt:: bash

   azul retrieve UGC11116 -r 1m --from pdr | azul process

.. figure:: _static/UGC11116.jpg

   A 2' x 2' field around `UGC 11116 <https://simbad.u-strasbg.fr/simbad/sim-basic?Ident=UGC+11116>`_.

   Credit: ESA Euclid/Euclid Consortium/NASA/Q1-2025/Antoine Basset (CNES)


License
-------

`Apache-2.0 <https://raw.githubusercontent.com/kabasset/azulero/refs/tags/v0.1.0/LICENSE>`_


How to help?
------------

* `Report bugs, request features <https://github.com/kabasset/azulero/issues>`_,
  tell us what you think of the tools and results...
* Share your images with us, we're curious!
* If you publish images rendered with this software, please credit:
  *Image processing with Azulero (Antoine Basset, CNES).*
* If you use this software for academic publications, please cite as follows:

.. code-block:: bibtex

   @software{Basset_Azulero,
     author = {Basset, Antoine and Schirmer, Mischa and Bouvard, Téo and Gimenez, Rollin and Nguyen-Kim, Kane and Candini, Gian Paolo and Malapert, Jean-Christophe},
     license = {Apache-2.0},
     title = {Azulero},
     version = {2.0},
     year = {2026},
     doi = {10.24400/815952/Azulero}
   }


Contributors
------------

Azulero is the result of many discussions and technical exchanges.

Mischa Schirmer (MPIA)
   Azulero's color blending is freely inspired by that of Mischa's script eummy_.
Téo Bouvard (Thales)
   Drafed :doc:`retrieve`.
Rollin Gimenez (CNES)
   Fixed packaging, early and long-term beta-tester.
Kane Nguyen-Kim (IAP)
   Provided URLs for retrieving public data, earliest and longest-term beta-tester!
Gian Paolo Candini (CSIC)
   Investigated rendering issues and improved parametrization.
   Drafted auto-tuning of :doc:`process`' white point.
Jean-Christophe Malapert (CNES)
   Implemented robust spatial queries on the sphere.


.. _eummy: https://github.com/schirmermischa/eummy
.. _euniverse: https://github.com/schirmermischa/euniverse
