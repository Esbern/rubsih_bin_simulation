# Geo / CRS transforms (`simulated_city.geo`)

This module provides **coordinate reference system (CRS)** transforms using `pyproj`.

It is kept optional so the template stays lightweight.


## Install

```bash
pip install -e ".[geo]"
```


## CRS constants

- `EPSG_4326` = WGS84 latitude/longitude (degrees)
- `EPSG_3857` = Web Mercator (meters, common for web maps)
- `EPSG_25832` = ETRS89 / UTM zone 32N (meters, good for Denmark)


## Convenience functions (recommended)

### `wgs2utm(lat, lon) -> (easting, northing)`

Converts **WGS84** `(lat, lon)` to **EPSG:25832** meters.

Example:

```python
from simulated_city.geo import wgs2utm

# Copenhagen City Hall (approx.)
e, n = wgs2utm(55.6761, 12.5683)
print(e, n)
```


### `utm2wgs(easting, northing) -> (lat, lon)`

Converts **EPSG:25832** meters back to **WGS84** `(lat, lon)`.

Example:

```python
from simulated_city.geo import utm2wgs

lat, lon = utm2wgs(724000.0, 6179000.0)
print(lat, lon)
```


## General-purpose transforms

### `transform_xy(x, y, from_crs=..., to_crs=...) -> (x2, y2)`

Transforms a single point between two CRS.

Important: internally we use `always_xy=True`, so **(x, y)** ordering is always:

- for WGS84 (EPSG:4326): `(lon, lat)`
- for projected CRSs: usually `(easting, northing)` or `(x, y)` meters

Example (WGS84 → UTM32):

```python
from simulated_city.geo import EPSG_25832, transform_xy

lat, lon = 55.6761, 12.5683
e, n = transform_xy(lon, lat, from_crs="EPSG:4326", to_crs=EPSG_25832)
print(e, n)
```


### `transform_many(xs, ys, from_crs=..., to_crs=...) -> (xs2, ys2)`

Transforms many points at once.

Example:

```python
from simulated_city.geo import transform_many

xs2, ys2 = transform_many([12.56, 12.57], [55.67, 55.68], from_crs="EPSG:4326", to_crs="EPSG:25832")
print(xs2[:2], ys2[:2])
```


## Web Mercator helpers

### `webmercator_to_epsg25832(x, y) -> (easting, northing)`

Example:

```python
from simulated_city.geo import webmercator_to_epsg25832

e, n = webmercator_to_epsg25832(1_000_000.0, 7_000_000.0)
print(e, n)
```


### `epsg25832_to_webmercator(easting, northing) -> (x, y)`

Example:

```python
from simulated_city.geo import epsg25832_to_webmercator

x, y = epsg25832_to_webmercator(724000.0, 6179000.0)
print(x, y)
```


## Internal helper (advanced)

`_get_transformer(from_crs, to_crs)` returns a cached `pyproj.Transformer`.
You normally don’t need to call it directly.
