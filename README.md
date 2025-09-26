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
azul [--workspace <workspace>] retrieve [--dsr <dataset_release>] <tile_indices>
azul [--workspace <workspace>] crop <tile_index>
azul [--workspace <workspace>] process <tile_slicing>
```

with:

* `<workspace>` - The parent directory to save everything, in which one folder per tile will be created (defaults to the current directory).
* `<dataset_release>` - The dataset release of the tiles to be downloaded (defaults to a list of known releases).
* `<tile_indices>` - The space-separated list of tiles to be downloaded.
* `<tile_index>` - A single tile index.
* `<tile_slicing>` - A single tile index, optionally followed by a slicing à-la NumPy.

Example:

```
azul retrieve 102034383 --dsr DR1_R1
azul crop 102034383
azul process 102034383[1000:9000,7500:13500]
```

# Algorithm

## Basics


```mermaid
---
config:
  sankey:
    showValues: false
---
sankey-beta

NIR median,L,100
I,L,100
I,B,20
Y,G,30
Y,B,80
H,R,100
J,G,70
```


We want to output an RGB image from four input channels: one VIS (I) and three NIR bands (Y, J, H).
We decide to keep the wavelength ordering: I < Y < J < H.
Two adjacent input channels may contribute to an output channel, e.g. Y and J may contribute to G.
An input channel may contribute to two adjacent output channels, e.g. Y may contribute to B and G.
Resolution in I is better than in other channels, therefore it has higher weight in the output intensity (more precisely, lightness).
Different weight parameters control the different contributions.

The dynamic range is arcsinh-scaled, which yields pleasing results for both low- and high-energy regions.
The function is linear-like for low values and log-like for high values.
Scaling is controlled by two bounds -- black and white points -- and a stretching parameter which sets the transition point between linear-like scaling and log-like scaling.

Bad pixels (those with extremely high values or null value in the input bands) are finally inpainted, either as white points or using biharmonic inpainting.
Inpainting is adequate for DEEP tiles, but ugly in some of the WIDE tiles.
Relying on bitmasks to decide on the inpainting technique would be better, especially for VIS ghosts, yet I did not find a satisfying selection method, which would work both for WIDE and DEEP tiles...

## Blending algorithm

Using:

* Upper case for arrays, lower case for scalars;
* VIS, NIR-Y, NIR-J, NIR-H channels as $I, Y, J, H$.
* Channel-wise gains $g_x$ for $x$ in $I, Y, J, H$;
* Weights $w_{Y,G}, w_{I, B}, w_{\text{NIR}, L}$ between 0 and 1;
* Linear interpolation function $\text{lerp}_l(x, y) := w_l \times y + (1 - w_l) \times y$;
* Stretching parameter $a$;
* Black and white points $b$ and $w$;
* $(a, b)$-clipping function $\text{clip}_{a, b}(x)$;
* Color space components $\text{hue}(r, g, b), \text{saturation}(r, g, b)$;

Do:

* Balancing: Multiply channels $I, Y, J, H$ by gains $g_I, g_Y, g_J, g_H$, respectively.
* Blending: Set
  * $R = H$,
  * $G = \text{lerp}_{Y, G}(Y, J)$,
  * $B = \text{lerp}_{I, B}(I, Y)$,
  * $L = \text{lerp}_{\text{NIR}, L}(\text{median}(Y, J, H), I)$.
* Stretching: Set
  * $x = \text{arcsinh}(x / a)$ for $x$ in $R, G, B, L, b, w$,
  * $x = \text{clip}_{0, 1}((x - b) / (w - b))$ for $x$ in $R, G, B, L$.
* Saturation: Set $S = g_S \times \text{saturation}(R, G, B)$.
* Remapping: Recompute $R, G, B$ from $\text{hue}(R, G, B), L, S$.

Default parameters give good resuts in the vast majority of cases.
For corner cases, check `azul process -h` and experiment!

# Advanced usage

One day I'll find some time to write something useful here... 🤔

In the meantime, please check help messages:

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
