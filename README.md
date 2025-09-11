![Logo](azul.png)

# Bring colors to Euclid tiles!

This program merges VIS and NIR observations over a MER tile.
It detects and inpaints bad pixels (hot and cold pixels, saturated stars...), and combines the 4 channels (I, Y, J, H) into an sRGB image.

# License

[Apache-2.0](LICENSE)

# Usage

```sh
export TILE=101835789
export DSR=DR1_R2

curl -s "https://eas-dps-rest-ops.esac.esa.int/REST?project=EUCLID&class_name=DpdMerBksMosaic&Data.TileIndex=$TILE&Header.DataSetRelease=DR1_R1&fields=Data.Filter.Name:Header.ProductId.LimitedString" | grep -e "VIS" -e "NIR" | cut -d, -f2 > ~/Downloads/$TILE.txt

mkdir ~/Downloads/$TILE

eden.3.1

E-Run ST_Operations ST_ArchiveClient --env ops --project EUCLID --with-files eas get --type DpdMerBksMosaic --id-file ~/Downloads/$TILE.txt --files-include 'EUC_MER_BGSUB*' --output ~/Downloads/$TILE

find ~/Downloads/$TILE -type f -name 'EUC_MER_BGSUB*' -exec gzip -d {} \;

python3 process.py ~/Downloads/$TILE output.tiff --white 100000
```
