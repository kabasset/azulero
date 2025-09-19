![Logo](https://raw.githubusercontent.com/kabasset/azulero/v0.1.0/azul.png)

# Bring colors to Euclid tiles!

Azul(ERO)* downloads and merges VIS and NIR observations over a MER tile.
It detects and inpaints bad pixels (hot and cold pixels, saturated stars...), and combines the 4 channels (I, Y, J, H) into an sRGB image.

*I started this project when Euclid EROs came out...

# License

[Apache-2.0](https://raw.githubusercontent.com/kabasset/azulero/refs/tags/v0.1.0/LICENSE)

# Disclamer

⚠️ **This is a beta version!** ⚠️

* The tool is far from perfect and can be frustrating.
* Error cases are not handled and messages may be cryptic or misleading.
* There is no documentation...
* Please make sure to read the "How to help?" section below before using this version.

# Installation and setup

Install the `azulero` package with:

```
pip install azulero
```

Setup the `~/.netrc` file for `eas-dps-rest-ops.esac.esa.int` and `euclidsoc.esac.esa.int` with your Euclid credentials:

```xml
machine eas-dps-rest-ops.esac.esa.int
  login <login>
  password <password>
machine euclidsoc.esac.esa.int
  login <login>
  password <password>
```

# Basic usage

1. Download the MER-processed FITS file of your tiles with `azul retrieve`.
2. Blend the channels and inpaint artifacts with `azul process`.

Usage:

```xml
azul [--workspace <workspace_dir>] retrieve [--dsr <dataset_release>] <tile_indices>
azul [--workspace <workspace_dir>] process <tile_index>
```

Example:

```
azul retrieve 101292159
azul process 101292159
```

# Advanced usage

One day I'll find some time to write something useful here... 🤔

# How to help?

* [Report bugs, request features](https://github.com/kabasset/azulero/issues), tell me what you think of the tool and results...
* Mention myself and/or `azulero` when you publish images processed with this tool.
* Let me know when you publish images with this tool, I'm curious!

# Acknowledgements

* Azul's color blending is freely inspired by that of Mischa Schirmer's `eummy.py`.
* Thank you Téo Bouvard for helping me drafting `retrieve`!
* Thank you Kane Nguyen-Kim (IAP) and Rollin Gimenez (CNES), early beta-testers...
* 🔥 Congratulations to the whole Euclid community; The mosaics are simply unbelievable!
* 😍 Thank you also for answering my dummy questions on the contents of the images I posted.
