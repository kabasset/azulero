![Logo](https://raw.githubusercontent.com/kabasset/azulero/v0.1.0/azul.png)

# Bring colors to Euclid tiles!

Azulero is a command line toolbox aimed at producing publication-ready color Euclid images.

The core of Azulero is the color rendering command `azul process`.
It enhances and combines all four Euclid photometric bands (VIS, NIR-Y, NIR-J, NIR-H) into an RGB image.
The process involves defect inpainting, PSF-aware sharpening, dynamic range stretching and blending.

Other commands implement many more features:

* `azul retrieve` finds and downloads individual photometric images from public or Euclid Consortium-internal data archives.
* `azul arrange` arranges collections of images into collages.
* `azul roam` produces pan-and-zoom videos and interfaces with Gaia Sky for integrating them into planetarium videos.

Pipelining makes batch processing simple, including with parallelization.

# License

[Apache-2.0](https://raw.githubusercontent.com/kabasset/azulero/refs/tags/v0.1.0/LICENSE)

# Documentation

[Homepage](https://kabasset.github.io/azulero/versions/index.html)

# Citation

[DOI: 10.24400/815952/Azulero](http://doi.org/10.24400/815952/Azulero)

Please refer to the output of command `azul cite`.
