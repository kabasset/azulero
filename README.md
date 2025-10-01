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
* Please make sure to read the "How to help?" section below before using this version.

# Installation and setup

Install the `azulero` package with:

```
pip install azulero
```

If you wish to access Euclid-internal data, setup the `~/.netrc` file for `eas-dps-rest-ops.esac.esa.int` and `euclidsoc.esac.esa.int` with your Euclid credentials:

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

* 📥 Download the MER-processed FITS file of your tiles with `azul retrieve`.
* ✂️ Optionally select the region to be processed with `azul crop`.
* 🌟 Blend the channels and inpaint artifacts with `azul process`.

Usage:

```xml
azul [--workspace <workspace>] retrieve [--dsr <dataset_release>] [--from <provider>] <tile_indices>
azul [--workspace <workspace>] crop <tile_index>
azul [--workspace <workspace>] process <tile_slicing>
```

with:

* `<workspace>` - The parent directory to save everything, in which one folder per tile will be created (defaults to the current directory).
* `<dataset_release>` - The dataset release of the tiles to be downloaded (defaults to a list of known releases).
* `<provider>` - The data archive name.
* `<tile_indices>` - The space-separated list of tiles to be downloaded.
* `<tile_index>` - A single tile index.
* `<tile_slicing>` - A single tile index, optionally followed by a slicing à-la NumPy.

# Example

Here is an example output and the commands which produced it below:

![processed](https://raw.githubusercontent.com/kabasset/azulero/develop/102159776.jpg)

> Credit: Antoine Basset, CNES/ESA Euclid/Euclid Consortium/NASA/Q1-2025

```
azul retrieve 102159776 --from sas
azul crop 102159776
azul process 102159776[5500:7500,5000:7000] -w 2000 --nirl 0.1 --jr 0.9 --ib 0.5 -a 0.5 -b -1
```
I have post-processed the output to my liking:

![postprocessed](https://raw.githubusercontent.com/kabasset/azulero/develop/102159776_post.jpg)

> Credit: Antoine Basset, CNES/ESA Euclid/Euclid Consortium/NASA/Q1-2025

> The two thick blue rings 💍 are artifacts of the VIS instrument known as ghosts.
> To my knowledge, the galaxy in the center has never been resolved this way.
> Rendering the image allowed me to discover this is a splendid polar-ring 💍 galaxy!
> The previously unseen golden structure top left may be an Einstein ring 💍 or a collisional ring 💍 -- the question remains open. 

As you can see, getting a nice image required a bit of parametrization.
This is because we are using the public Q1 data.
DR1 data, to be published in 2026, have a much better signal-to-noise ratio, and default parameters give very good results.
I already rendered the DR1 version of this field; I cannot share it today, but I can already tell you it is mesmerizing 😏

# Advanced usage

One day I'll find some time to write something useful here... 🤔

In the meantime, please read [the algorithm description](algo.md) and check help messages:

```
azul -h
azul retrieve -h
azul crop -h
azul process -h
```

# How to help?

* [Report bugs, request features](https://github.com/kabasset/azulero/issues), tell me what you think of the tool and results...
* Mention myself (Dr Antoine Basset, CNES) and/or [`azulero`](https://pypi.org/project/azulero/) when you publish images processed with this tool.
* Share with me your images, I'm curious!

# Contributors

* Dr Mischa Schirmer (MPIA): Azul's color blending is freely inspired by that Mischa's script `eummy.py`.
* Téo Bouvard (Thales): drafed `retrieve`.
* Rollin Gimenez (CNES): Fixed packaging.
* Kane Nguyen-Kim (IAP): Provided URLs for retrieving public data.

# Acknowledgements

* 🔥 Congratulations to the whole Euclid community; The mosaics are simply unbelievable!
* 😍 Thank you also for answering my dummy questions on the contents of the images I posted.
