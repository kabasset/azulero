# Retrieve

## Basics

The input of `azul process` (individual MER mosaics) can be downloaded with `azul retrieve`.
The command takes as parameter the tile index, and optionally the data provider and some metadata like the dataset release.
The files are downloaded in the [workspace](workspace.md), in a folder named after the tile index.

## Data providers

There are currently two data providers:

* `dps` for Euclid-internal data and
* `sas` for public data.

We intend to add support to the internal SAS instance soon.
