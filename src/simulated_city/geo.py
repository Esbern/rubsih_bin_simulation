from __future__ import annotations

"""Geospatial helpers.

This module provides small, workshop-friendly helpers for transforming
coordinates between common projected coordinate reference systems (CRS).

Why these two?
- **EPSG:3857** (Web Mercator) is commonly used for web map display.
- **EPSG:25832** (ETRS89 / UTM zone 32N) is useful for coordinate
  manipulations because units are meters.

Dependency note:
This module uses `pyproj` for accurate CRS transforms. The dependency is kept
optional so the template stays lightweight.

Install with:

    pip install -e ".[geo]"
"""

from functools import lru_cache
from typing import Iterable


EPSG_3857 = "EPSG:3857"
EPSG_25832 = "EPSG:25832"
EPSG_4326 = "EPSG:4326"


def wgs2utm(lat: float, lon: float) -> tuple[float, float]:
        """Convert WGS84 latitude/longitude to EPSG:25832 (UTM32) meters.

        Parameters
        - lat, lon: WGS84 latitude/longitude in degrees

        Returns
        - (easting, northing) in meters (EPSG:25832)

        Notes
        - Internally, pyproj expects (x, y) ordering. For EPSG:4326 that is
            (lon, lat), which is why this calls :func:`transform_xy` with (lon, lat).
        """

        easting, northing = transform_xy(lon, lat, from_crs=EPSG_4326, to_crs=EPSG_25832)
        return easting, northing


def utm2wgs(easting: float, northing: float) -> tuple[float, float]:
        """Convert EPSG:25832 (UTM32) meters to WGS84 latitude/longitude.

        Returns
        - (lat, lon) in degrees (EPSG:4326)
        """

        lon, lat = transform_xy(easting, northing, from_crs=EPSG_25832, to_crs=EPSG_4326)
        return lat, lon


def webmercator_to_epsg25832(x: float, y: float) -> tuple[float, float]:
    """Convert a point from EPSG:3857 (Web Mercator) to EPSG:25832."""

    return transform_xy(x, y, from_crs=EPSG_3857, to_crs=EPSG_25832)


def epsg25832_to_webmercator(easting: float, northing: float) -> tuple[float, float]:
    """Convert a point from EPSG:25832 to EPSG:3857 (Web Mercator)."""

    return transform_xy(easting, northing, from_crs=EPSG_25832, to_crs=EPSG_3857)


def transform_xy(x: float, y: float, *, from_crs: str = EPSG_3857, to_crs: str = EPSG_25832) -> tuple[float, float]:
    """Transform a single (x, y) coordinate between two CRS.

    Parameters
    - x, y: coordinates in the source CRS
    - from_crs: CRS identifier like "EPSG:3857"
    - to_crs: CRS identifier like "EPSG:25832"
    """

    transformer = _get_transformer(from_crs, to_crs)
    tx, ty = transformer.transform(x, y)
    return float(tx), float(ty)


def transform_many(
    xs: Iterable[float],
    ys: Iterable[float],
    *,
    from_crs: str = EPSG_3857,
    to_crs: str = EPSG_25832,
) -> tuple[list[float], list[float]]:
    """Transform many points.

    Returns two lists: (xs_out, ys_out).
    """

    transformer = _get_transformer(from_crs, to_crs)
    xs_out: list[float] = []
    ys_out: list[float] = []
    for x, y in zip(xs, ys, strict=False):
        tx, ty = transformer.transform(x, y)
        xs_out.append(float(tx))
        ys_out.append(float(ty))
    return xs_out, ys_out


@lru_cache(maxsize=32)
def _get_transformer(from_crs: str, to_crs: str):
    """Return a cached pyproj Transformer.

    The `always_xy=True` setting forces consistent axis ordering (x, y).
    """

    try:
        from pyproj import CRS, Transformer  # type: ignore[import-not-found]
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "pyproj is required for simulated_city.geo coordinate transforms. "
            "Install it with `pip install -e \".[geo]\"` (or `pip install pyproj`)."
        ) from e

    return Transformer.from_crs(CRS.from_user_input(from_crs), CRS.from_user_input(to_crs), always_xy=True)
