"""Demo: Folium web map (Copenhagen City Hall).

This mirrors the notebook web map section, but as a plain script.

- Uses WGS84 lat/lon directly (no CRS transforms)
- Saves an HTML file you can open in your browser

Run:
    python scripts/demo/03_folium_map_city_hall.py

Requires:
    pip install -e ".[notebooks]"  (or: pip install folium)
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    # Approximate point near Copenhagen City Hall (Rådhuspladsen).
    lat, lon = 55.6761, 12.5683

    try:
        import folium  # type: ignore
    except ModuleNotFoundError:
        print("folium is not installed.")
        print("Install with: pip install -e \".[notebooks]\"  (or: pip install folium)")
        return

    m = folium.Map(location=[lat, lon], zoom_start=18, tiles="OpenStreetMap")
    popup = folium.Popup(f"WGS84 (lat, lon): {lat:.6f}, {lon:.6f}", max_width=300)
    folium.Marker([lat, lon], popup=popup, tooltip="Copenhagen City Hall (approx)").add_to(m)

    out_path = Path("copenhagen_city_hall_map.html").resolve()
    m.save(str(out_path))
    print("Saved map HTML:", out_path)
    print("Open it in your browser:", out_path.as_uri())


if __name__ == "__main__":
    main()
