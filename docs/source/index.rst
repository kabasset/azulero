.. raw:: html

   <img src="_static/favicon.png" class="align-left" style="height: 40px; margin: 0 16px 0 0 !important"/>

Azulero |version|
=================

.. toctree::
   :maxdepth: 1
   :hidden:

   self
   primer
   news
   quickstart
   interfaces
   retrieve
   process
   crop
   arrange
   roam
   pipelines
   python
   changes
   devnotes
   ai

.. thumbnail:: _static/collage_266.0955154946042,66.96054615038162_102159772_ESO482-009_102045468.png
   :width: 120px
   :align: right


Bring colors to Euclid tiles!
-----------------------------

Azulero is a toolbox for producing publication-ready color Euclid images.

It cleans and enhances MER data and combines the four Euclid photometric channels (I, Y, J, H) into an RGB image.
Input data are retrieved from public or private archives, and post-processing commands produce mesmerizing collages and flowing videos.

Azulero is now compatible with Unix and Windows pipelines, which makes batch processing simple,
including with parallelization (see :doc:`pipelines`).
As an example, the collage on the right is the unedited output of a single command line
(credit: ESA Euclid / Euclid Consortium / NASA / Q1-2025 / Antoine Basset, CNES).


License
-------

The source code is licensed under |license| (see the SPDX_ page for details).


How to help?
------------

The most straightforward way to help us is to `report bugs and request features <https://github.com/kabasset/azulero/issues>`_!
We view usability as a priority, always try to deliver clean interfaces, and value your feedback.
Please tell us what you think of the tools and results.
Also, feel free to share your images with us, we're curious and learn a lot from the experience of users.

Azulero is partly funded by public agencies -- most notably `CNES <https://cnes.fr/en>`_.
Using public money for development means we must deliver something meaningful and accessible.
Azulero is a tiny piece of non-critical software,
but we hope it contributes to making Euclid an exceptional mission which benefits to everyone, and we hope you feel the same!
In this case, please do not forget to acknowledge the toolbox
-- it really matters to show our managers Azulero is useful and must be maintained.
If you publish images rendered with this software, please credit: *Image processing with Azulero (Antoine Basset, CNES).*
If you use this software for academic publications, please cite as follows:

.. code-block:: bibtex

   @software{Basset_Azulero,
     author = {Basset, Antoine and Schirmer, Mischa and Bouvard, Téo and Gimenez, Rollin and Nguyen-Kim, Kane and Candini, Gian Paolo and Malapert, Jean-Christophe and Wozny, Nicolas and Golawska, Hanna},
     license = {Apache-2.0},
     title = {Azulero},
     version = {2.0},
     year = {2026},
     doi = {10.24400/815952/Azulero}
   }


Contributors
------------

Azulero is the result of so many discussions and technical exchanges.
Here is the exhaustive list of contributors and their contributions.

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
Nicolas Wozny (IAP)
   Investigated SAS retrieval failures, drafted workarounds.
Hanna Golawska (ESA)
   Provided feedback and support for the integration in ESA Datalabs.

In addition to these direct contributions, we would like to thank the Euclid community very warmly
for the support they showed and the quick and surprisingly detailed answers they gave to our sometimes dummy questions.
It is a real pleasure and an extraordinary journey working in such a collaboration
with so many world-renowned experts and brilliant newcomers.


.. _eummy: https://github.com/schirmermischa/eummy
.. _euniverse: https://github.com/schirmermischa/euniverse
