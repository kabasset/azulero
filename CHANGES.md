# 1.2.0

## New features

`azul find`

* FITS files and WCS files are supported as input with option `--wcs`,
  in which case the location is returned in pixel coordinates,
  and an `azul process` command is proposed to process the region around the location.

`azul process`

* Outputs can be saved as FITS files, in which case WCS records are written to the header.
* For all output formats, a WCS file can be saved with option `--wcs`.

`azul roam`

* A FITS file or WCS file can be passed to option `--wcs`.
* Equirectangular images are supported as input.
* Gaia Sky is supported as input.
* RA/dec coordinates are supported for equirectangular images, Gaia Sky, or with option `--wcs`.
* Zoom can be specified as a horizontal field of view for equirectangular images, Gaia Sky, or with option `--wcs`.
* Low-pass filter is applied for wide fields of view to prevent aliasing.

## Improvements

`azul process`

* Arbitrary output paths can be configured with new placeholder `{workspace}`.

`azul roam`

* Output name is built from input names.
* Default FPS is 25.

## Optimization

`azul roam`

* Image pyramids are built to speed up rendering of frames with wide fields of view.

## Known issues

`azul roam`

* kabasset/azulero/#55 Zoom < 1° is not supported.

# 1.1.1

## Bug fixes

`azul process`

* Command did crash when output template contained `{step}`.

# 1.1.0

## Bug fixes

`azul crop`

* Command did crash when reading the image.

## New features

`azul retrieve`

* New, SAS-based data provider for Internal Data Releases (default provider).

## Improvements

`azul process`

* Stacking of multiple inputs per channel relies on median instead of mean.
* Ouput(s) can be written anywhere, not only in the tile folder.

## Optimization

`azul process`

* Inpainting is a bit less memory-greedy.

# 1.0.0

## Initial features

`azul find`

* [Requires internet] Find object coordinates.
* [Euclid members] Find index of tiles containing given objects or coordinates.

`azul retrieve`

* [Requires internet] Download input data for a collection of tiles.

`azul crop`

* Select the region to be rendered with a rudimentary graphical interface.

`azul process`

* Render a color image from MER data.

`azul roam`

* Produce a pan-and-zoom video from an image.

## Known issues

`azul find`

* kabasset/azulero#35 - Cartesian coordinates are used, which cannot handle positions around RA = 0° = 360° or dec = +/-90° (where there are no Euclid data anyway).

`azul process`

* kabasset/azulero#16 - Inpainted saturated pixel are rendered too dim.
* kabasset/azulero#19 - Missing values are badly handled when multiple inputs are provided for a channel.

`azul roam`

* kabasset/azulero#31 - Zoom > 100% is not supported.
