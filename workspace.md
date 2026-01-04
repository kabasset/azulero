# Workspace

## Basics

Azul commands (except `azul roam`) assume inputs are located in a workspace which contains a folder per tile, named after its index,
as well as configuration files such as the GeoJson file which lists available MER mosaics for `azul find`.
By default, output files will also be written to the tile folders.

## Example

Here is an example workspace in which tile 102159776 was retrieved and processed (the input file names are shortened for readability).
Here, files `roam.yaml` and `102159776_roaming.mp4` are respectively the configuration and output of `azul roam`.

```sh
workspace
├── 102159776
│   ├── EUC_MER_BGSUB-MOSAIC-NIR-H_TILE102159776.fits
│   ├── EUC_MER_BGSUB-MOSAIC-NIR-J_TILE102159776.fits
│   ├── EUC_MER_BGSUB-MOSAIC-NIR-Y_TILE102159776.fits
│   ├── EUC_MER_BGSUB-MOSAIC-VIS_TILE102159776.fits
│   ├── 102159776_mask.tiff
│   ├── 102159776_blended.tiff
│   ├── 102159776_adjusted.tiff
│   ├── roaming.yaml
│   └── 102159776_roaming.mp4
└── DpdMerFinalCatalog.geojson
```
