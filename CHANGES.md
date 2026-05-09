# 2.0

## Breaking changes

* The following commands are deprecated:
  * `find` (merged into `retrieve`),
  * `crop` (partially replaced with cutout retrieval, to be fully replaced later),
  * `assemble` (previously experimental, replaced with `arrange`),
  * `tune` (previously experimental, to be merged into `process` later).

`azul retrieve`

* Data provider `sas` was renamed as `pdr`.

`azul process`

* Default dynamic range parameters were updated to increase SNR.
* Option `--wcs` was removed:
  * For FITS files, standard WCS records are used;
  * For TIFF files, the parameters are saved as standard metadata;
  * For other formats, the parameters are written following the output name with extension `.wcs`.

`azul roam`

* The key frames file is passed as a named option.

## Bug fixes

`azul process`

* In some systems and environments, the script was crashing when `--wcs` was enabled and no slicing was performed.
* Masked saturated stars were rendered too dim.

## New features

* The following commands were added: `arrange`, `cite`.
* The following commands support piping:
  * `retrieve` can read targets from `stdin`, write workdirs to `stdout`,
  * `process` can read workdirs from `stdout`, write render filenames to `stdout`,
  * `arrange` can read inputs from `stdin`, write collage filename to `stdout`,
  * `roam` can read input from `stdin`, write video filename to `stdout`.
* Default arguments can be overloaded with environment variables.

`azul retrieve`

* Retrieve named objects.
* Retrieve coordinates.
* Retrieve cutouts (option `-r`).
* Option `-n` limits the number of tiles per target.
* Option `-q` performs queries only (no download).
* Option `-f` with no argument forces all downloads.

`azul process`

* Process a sequence of workdirs.
* Accept workdirs with subfolders.
* Clipping is enabled by `--curves`.

`azul arrange`

* Arrange a collection of images into a regular grid.

`azul roam`

* Add WCS to planar projection.

`azul cite`

* Print citation instructions.

## Cleaning

* Logs are written to `stderr` with a proper logger, which also supports log levels (option `--log`).
* Documentation uses proper HTML pages (which include CLI documentation).
* Video tutorials are published.
* Packaging is handled with `uv`.
* Merged `AstroQuery` class into `SAS`.
* Pixel ordering is consistent.

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

`azul find`

* kabasset/azulero#35 - Cartesian coordinates are used,
  which cannot handle positions around RA = 0° = 360° or dec = +/-90°
  (where there are no Euclid data anyway).

`azul process`

* kabasset/azulero#16 - Inpainted saturated pixel are rendered too dim.

`azul roam`

* kabasset/azulero#55 - Zoom < 1° is not supported for Gaia Sky.
* kabasset/azulero#31 - Zoom > 100% is not supported.

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
