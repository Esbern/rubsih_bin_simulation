import pytest


def test_webmercator_utm32_roundtrip() -> None:
    pyproj = pytest.importorskip("pyproj")
    assert pyproj  # keep linters happy

    from simulated_city.geo import (
        EPSG_25832,
        EPSG_3857,
        transform_xy,
    )

    # A plausible Web Mercator point (meters), not too close to the poles.
    x0, y0 = 1_000_000.0, 7_000_000.0

    e, n = transform_xy(x0, y0, from_crs=EPSG_3857, to_crs=EPSG_25832)
    x1, y1 = transform_xy(e, n, from_crs=EPSG_25832, to_crs=EPSG_3857)

    assert x1 == pytest.approx(x0, abs=1e-6)
    assert y1 == pytest.approx(y0, abs=1e-6)


def test_wgs2utm_utm2wgs_roundtrip_copenhagen_city_hall() -> None:
    pyproj = pytest.importorskip("pyproj")
    assert pyproj  # keep linters happy

    from simulated_city.geo import utm2wgs, wgs2utm

    # Copenhagen City Hall (approx.)
    lat0 = 55.67597
    lon0 = 12.56984

    e, n = wgs2utm(lat0, lon0)
    lat1, lon1 = utm2wgs(e, n)

    # Round-trip should be very close.
    assert lat1 == pytest.approx(lat0, abs=1e-6)
    assert lon1 == pytest.approx(lon0, abs=1e-6)
