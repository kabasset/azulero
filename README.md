![Logo](azul.png)

# Bring colors to Euclid tiles!

Azul(ERO)* downloads and merges VIS and NIR observations over a MER tile.
It detects and inpaints bad pixels (hot and cold pixels, saturated stars...), and combines the 4 channels (I, Y, J, H) into an sRGB image.

*I started this project when Euclid EROs came out...

# License

[Apache-2.0](LICENSE)

# Installation and setup

Install the `azulero` package with:

```
pip install azulero
```

Setup the `.netrc` file for `eas-dps-rest-ops.esac.esa.int` and `euclidsoc.esac.esa.int` with your Euclid credentials:

```xml
machine eas-dps-rest-ops.esac.esa.int
  login <login>
  password <password>
machine euclidsoc.esac.esa.int
  login <login>
  password <password>
```

# Basic usage

1. Download the MER-processed FITS file of your tiles with `azul retrieve`.
2. Blend the channels and inpaint artifacts with `azul process`.

Usage:

```xml
azul [--workspace <workspace_dir>] retrieve [--dsr <dataset_release>] <tile_indices>
azul [--workspace <workspace_dir>] process <tile_index>
```

Example:

```
azul retrieve 101292159
azul process 101292159
```

# Advanced usage

One day I'll find some time to write something useful here...

# How to help?

* [Report bugs, request features](https://github.com/kabasset/azulero/issues), tell me what you think of the tool and results...
* Mention `kabasset/azulero` when you publish images processed with this tool.
* Let me know when you publish images with this tool, I'm curious!
