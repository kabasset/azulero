# Retrieve

## Basics

The input of `azul process` (individual MER mosaics) can be downloaded with `azul retrieve`.
The command takes as parameter the tile index, and optionally the data provider and some metadata like the dataset release.
The files are downloaded in the [workspace](workspace.md), in a folder named after the tile index.

The data provider is specified with option `--from`, and may require authentication.
The available providers are described in the following sections.

## Public data

The public Science Archive System (SAS) provides access to public data and does not require any account.
It is triggered with option `--from sas`.

## Internal Data Releases

The private interface of the SAS (`easidr.esac.esa.int`) enables access to Internal Data Releases (IDRs).
A SAS account is needed and must be set up in the netrc configuration file, `~/.netrc` (or `_netrc` on Windows), as follows:

```xml
machine easidr.esac.esa.int
  login <login>
  password <password>
```

## DPS

Before they reach the SAS, products and datafiles are stored in the EAS-DPS and an EAS-DSS, respectively.
To reach them, an EAS account is needed and authentication must be configured in `~/.netrc` (or `_netrc` on Windows):

```xml
machine eas-dps-rest-ops.esac.esa.int
  login <login>
  password <password>
machine euclidsoc.esac.esa.int
  login <login>
  password <password>
```

Note that this provider is much slower than `idr`.
It is enabled with `--from dps`.
