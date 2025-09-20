![Logo](https://raw.githubusercontent.com/kabasset/azulero/v0.1.0/azul.png)

# Bring colors to Euclid tiles!

Azul(ero)* downloads and merges VIS and NIR observations over a MER tile.
It detects and inpaints bad pixels (hot and cold pixels, saturated stars...), and combines the 4 channels (I, Y, J, H) into an sRGB image.

*I started this project when Euclid EROs came out...

# License

[Apache-2.0](https://raw.githubusercontent.com/kabasset/azulero/refs/tags/v0.1.0/LICENSE)

# Disclaimer

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

The typical workflow is as follows:

* Download the MER-processed FITS file of your tiles with `azul retrieve`.
* Optionally select the region to be processed with `azul crop`.
* Blend the channels and inpaint artifacts with `azul process`.

Usage:

```xml
azul [--workspace <workspace>] retrieve [--dsr <dataset_release>] <tile_indices>
azul [--workspace <workspace>] crop <tile_index>
azul [--workspace <workspace>] process <tile_slicing>
```

with:

* `<workspace>` - The parent directory to save everything, in which one folder per tile will be created (defaults to the current directory).
* `<dataset_release>` - The dataset release of the tiles to be downloaded (defaults to `DR1_R1`).
* `<tile_indices>` - The space-separated list of tiles to be downloaded.
* `<tile_index>` - A single tile index.
* `<tile_slicing>` - A single tile index, optionally followed by a slicing à-la NumPy.

Example:

```
azul retrieve 102034383 --dsr DR1_R2
azul show 102034383
azul process 102034383[1000:9000,7500:13500]
```

# Advanced usage

One day I'll find some time to write something useful here... 🤔

# How to help?

* [Report bugs, request features](https://github.com/kabasset/azulero/issues), tell me what you think of the tool and results...
* Mention myself (Dr Antoine Basset, CNES) and/or [`azulero`](https://pypi.org/project/azulero/) when you publish images processed with this tool.
* Share with me your images, I'm curious!

# Acknowledgements

* Azul's color blending is freely inspired by that of Mischa Schirmer's `eummy.py`.
* Thank you Téo Bouvard for helping me drafting `retrieve`!
* Thank you Kane Nguyen-Kim (IAP) and Rollin Gimenez (CNES), early beta-testers...
* 🔥 Congratulations to the whole Euclid community; The mosaics are simply unbelievable!
* 😍 Thank you also for answering my dummy questions on the contents of the images I posted.
