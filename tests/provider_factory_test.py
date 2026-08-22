# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from azulero.providers import factory, tiling, cutout


class MinimalProvider:
    def __init__(self, user):
        self.user = user

    def query_tile_datafiles(self, tile) -> dict[str, str]:
        return {}

    def download_datafile(self, name: str, path: Path):
        pass


class MinimalSpatialProvider(MinimalProvider):

    def __init__(self, user):
        super().__init__(user)

    def query_tile_attributes(self, index) -> list[tiling.Tile]:
        return []

    def query_radec_tiles(self, radec, dsrs, modes) -> list[tiling.Tile]:
        return []


class CompleteProvider(MinimalSpatialProvider):

    def __init__(self, user):
        super().__init__(user)

    def download_cutout(self, name, path, center, radius):
        pass


factory.product_databases["minimal"] = lambda user: MinimalProvider(user)
factory.product_databases["spatial"] = lambda user: MinimalSpatialProvider(user)
factory.product_databases["complete"] = lambda user: CompleteProvider(user)


def test_minimal():
    tiling_file = Path(__file__).parent / "data/DpdMerFinalCatalog.geojson"
    provider = factory.DataProvider("minimal", tiling_file=tiling_file)
    assert isinstance(provider.product_db, MinimalProvider)
    assert isinstance(provider.tiling_db, tiling.Tiling)
    assert isinstance(provider.data_store, cutout.LocalCutout)


def test_spatial():
    provider = factory.DataProvider("spatial")
    assert isinstance(provider.product_db, MinimalSpatialProvider)
    assert isinstance(provider.tiling_db, MinimalSpatialProvider)
    assert isinstance(provider.data_store, cutout.LocalCutout)


def test_complete():
    provider = factory.DataProvider("complete")
    assert isinstance(provider.product_db, CompleteProvider)
    assert isinstance(provider.tiling_db, CompleteProvider)
    assert isinstance(provider.data_store, CompleteProvider)
