"""Demo: CRS transforms (WGS84 ↔ EPSG:25832).

This mirrors the notebook CRS cell and shows two approaches:

A) General transform_xy(...) (you must remember axis order for EPSG:4326)
B) Convenience helpers wgs2utm(...) / utm2wgs(...) (beginner-friendly)

Run:
    python scripts/demo/02_geo_crs_transforms.py

Requires:
    pip install -e ".[geo]"
"""

from __future__ import annotations

from simulated_city.geo import EPSG_25832, transform_xy, utm2wgs, wgs2utm


def main() -> None:
    # Approximate point near Copenhagen City Hall (Rådhuspladsen).
    lat, lon = 55.6761, 12.5683
    print("Start (WGS84 lat, lon):", (lat, lon))

    try:
        print("\n--- Version A: transform_xy (note axis order) ---")
        # Note: transforms use (x, y) = (lon, lat) when converting to/from EPSG:4326.
        e_a, n_a = transform_xy(lon, lat, from_crs="EPSG:4326", to_crs=EPSG_25832)
        print("To EPSG:25832 (E, N) [m]:", (e_a, n_a))

        lon_back_a, lat_back_a = transform_xy(e_a, n_a, from_crs=EPSG_25832, to_crs="EPSG:4326")
        print("Back to WGS84 (lat, lon):", (lat_back_a, lon_back_a))

        print("\n--- Version B: convenience helpers (beginner-friendly) ---")
        e_b, n_b = wgs2utm(lat, lon)
        print("To EPSG:25832 (E, N) [m]:", (e_b, n_b))

        lat_back_b, lon_back_b = utm2wgs(e_b, n_b)
        print("Back to WGS84 (lat, lon):", (lat_back_b, lon_back_b))

        print("\n--- Compare results (A vs B) ---")
        print("ΔE (m):", e_b - e_a)
        print("ΔN (m):", n_b - n_a)
        print("Round-trip error via helpers (degrees):", (lat_back_b - lat, lon_back_b - lon))
    except ModuleNotFoundError as e:
        print(str(e))
        print("Install with: pip install -e \".[geo]\"  (or: pip install pyproj)")


if __name__ == "__main__":
    main()
