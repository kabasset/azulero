![Logo](azul.png)

# Bring colors to Euclid tiles!

Command `azul process` merges VIS and NIR observations over a MER tile.
It detects and inpaints bad pixels (hot and cold pixels, saturated stars...), and combines the 4 channels (I, Y, J, H) into an sRGB image.
Command `azul retrieve` downloads the input data (VIS and NIR channels) of a MER tile.

# License

[Apache-2.0](LICENSE)

# Dependencies

* python3
* astropy
* numpy
* opencv-python
* requests (for `retrieve.py` only)
* scikit-image
* tifffile

# Basic usage

1. `pip install azulero` (I started this project at Euclid ERO time).
2. Setup the `.netrc` file for `eas-dps-rest-ops.esac.esa.int` and `euclidsoc.esac.esa.int` with your Euclid credentials (once for all).
3. Download the MER-processed FITS file of your tiles with `azul retrieve`.
4. Blend the channels and inpaint artifacts with `azul process`.

Usage:

```
azul [--workspace <workspace_dir>] retrieve [--dsr <dataset_release>] <space_separated_tile_indices>
aztl [--workspace <workspace_dir>] process <tile_index>
```

Example:

```
azul retrieve 101292159
azul process 101292159
```

# Advanced usage

One day I'll find some time to write something useful here...
