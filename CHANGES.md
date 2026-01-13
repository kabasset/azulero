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

## Expected features in 1.1.0

`azul find`

* kabasset/azulero#40 - Enable tile finding from SAS for public data.

`azul process`

* kabasset/azulero#44 - Reduce memory footprint.

`azul roam`

* kabasset/azulero#34 - Specify angle with respect to motion direction.
