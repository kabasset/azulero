# Retrieve

## Basics

The input of `azul process` (individual MER mosaics) can be downloaded with `azul retrieve`.
The command takes as parameter the tile index, and optionally the data provider and some metadata like the dataset release.
The files are downloaded in the [workspace](workspace.md), in a folder named after the tile index.

## Data providers

The data provider is specified with option `--from`.
The available providers are:

* `sas` for public data. No account is needed.
* `idr` for internal data releases.
  An EAS-SAS account is needed and [must be set up](README.md).
* `dps` to get Euclid-internal data before they reach the internal SAS.
  An EAS-DPS account is needed and [must be set up](README.md).
  This provider is much slower than `idr`.
