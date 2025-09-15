![Logo](azul.png)

# Bring colors to Euclid tiles!

Script `process.py` merges VIS and NIR observations over a MER tile.
It detects and inpaints bad pixels (hot and cold pixels, saturated stars...), and combines the 4 channels (I, Y, J, H) into an sRGB image.

Tools `spot.py` and `retrieve.py` are respectively aimed at selecting and downloading input data.

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

1. Setup the `.netrc` file for `eas-dps-rest-ops.esac.esa.int` and `euclidsoc.esac.esa.int` with your Euclid credentials (once for all).
2. Download the MER-processed FITS file of your tiles with `retrieve.py`.
3. Blend the channels and inpaint artifacts with `process.py`.

```
python3 retrieve.py 101292159
python3 process.py 101292159
```
