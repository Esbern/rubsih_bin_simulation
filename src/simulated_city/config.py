from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml


@dataclass(frozen=True, slots=True)
class MqttConfig:
    host: str
    port: int
    tls: bool
    username: str | None
    password: str | None = field(repr=False)
    client_id_prefix: str
    keepalive_s: int
    base_topic: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    mqtt: MqttConfig
    simulation: "SimulationConfig | None" = None


@dataclass(frozen=True, slots=True)
class SimulationLocationConfig:
    location_id: str
    lat: float
    lon: float


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Configuration for the rubbish-bin simulation.

    Notes
    - This section is optional; the template can be used without any simulation.
    - We keep the config immutable (frozen dataclasses) so it behaves like a
      simple value object.
    """

    timestep_minutes: int = 15
    arrival_prob: float = 0.25
    bag_fill_delta_pct: int = 2
    status_boundary_pct: int = 10
    # If true, emit a status event on every successful deposit (more frequent).
    # If false, emit only when crossing each N% boundary.
    publish_every_deposit: bool = False
    step_delay_s: float = 0.0
    # Optional: fixed simulation start timestamp (UTC) for deterministic logs.
    # If None, the simulator uses the current wall-clock time.
    start_time: datetime | None = None
    seed: int | None = None
    locations: tuple[SimulationLocationConfig, ...] = ()


def _parse_utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
    else:
        raise ValueError("simulation.start_time must be an ISO-8601 datetime string")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    # Load a local .env if present (it is gitignored by default).
    # This makes workshop setup easier while keeping secrets out of git.
    load_dotenv(override=False)

    resolved_path = _resolve_default_config_path(path)
    data = _load_yaml_dict(resolved_path)
    mqtt = data.get("mqtt") or {}
    simulation = data.get("simulation")

    host = str(mqtt.get("host") or "localhost")
    port = int(mqtt.get("port") or 1883)
    tls = bool(mqtt.get("tls") or False)

    username_env = mqtt.get("username_env")
    password_env = mqtt.get("password_env")
    username = os.getenv(str(username_env)) if username_env else None
    password = os.getenv(str(password_env)) if password_env else None

    client_id_prefix = str(mqtt.get("client_id_prefix") or "simcity")
    keepalive_s = int(mqtt.get("keepalive_s") or 60)
    base_topic = str(mqtt.get("base_topic") or "simulated-city")

    sim_cfg = _parse_simulation_config(simulation)

    return AppConfig(
        mqtt=MqttConfig(
            host=host,
            port=port,
            tls=tls,
            username=username,
            password=password,
            client_id_prefix=client_id_prefix,
            keepalive_s=keepalive_s,
            base_topic=base_topic,
        ),
        simulation=sim_cfg,
    )


def _parse_simulation_config(raw: Any) -> SimulationConfig | None:
    """Parse the optional `simulation:` section from config.yaml.

    We keep this tolerant: missing or empty simulation config returns None.
    """

    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Config key 'simulation' must be a mapping")

    timestep_minutes = int(raw.get("timestep_minutes") or 15)
    arrival_prob = float(raw.get("arrival_prob") or 0.25)
    bag_fill_delta_pct = int(raw.get("bag_fill_delta_pct") or 2)
    status_boundary_pct = int(raw.get("status_boundary_pct") or 10)

    publish_every_deposit = bool(raw.get("publish_every_deposit") or False)

    # Optional wall-clock delay between timesteps (useful for MQTT testing).
    step_delay_raw = raw.get("step_delay_s")
    if step_delay_raw is None:
        step_delay_raw = raw.get("step_delay_seconds")
    step_delay_s = float(step_delay_raw) if step_delay_raw is not None else 0.0

    start_time_raw = raw.get("start_time")
    start_time = _parse_utc_datetime(start_time_raw) if start_time_raw is not None else None

    seed_raw = raw.get("seed")
    seed = int(seed_raw) if seed_raw is not None else None

    locations_raw = raw.get("locations") or []
    if not isinstance(locations_raw, list):
        raise ValueError("Config key 'simulation.locations' must be a list")

    locations: list[SimulationLocationConfig] = []
    for item in locations_raw:
        if not isinstance(item, dict):
            raise ValueError("Each item in 'simulation.locations' must be a mapping")

        location_id = str(item.get("id") or item.get("location_id") or "").strip()
        if not location_id:
            raise ValueError("Each simulation location must have an 'id'")

        if "lat" not in item or "lon" not in item:
            raise ValueError(f"Simulation location '{location_id}' must define 'lat' and 'lon'")
        lat = float(item["lat"])
        lon = float(item["lon"])

        locations.append(SimulationLocationConfig(location_id=location_id, lat=lat, lon=lon))

    return SimulationConfig(
        timestep_minutes=timestep_minutes,
        arrival_prob=arrival_prob,
        bag_fill_delta_pct=bag_fill_delta_pct,
        status_boundary_pct=status_boundary_pct,
        publish_every_deposit=publish_every_deposit,
        step_delay_s=step_delay_s,
        start_time=start_time,
        seed=seed,
        locations=tuple(locations),
    )


def _load_yaml_dict(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}

    content = p.read_text(encoding="utf-8")
    loaded = yaml.safe_load(content)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file {p} must contain a YAML mapping at top level")
    return loaded


def _resolve_default_config_path(path: str | Path) -> Path:
    """Resolve a config path in a notebook-friendly way.

    When `load_config()` is called with the default relative filename
    (`config.yaml`), users often run code from a subdirectory (e.g. `notebooks/`).
    In that case we search parent directories so `config.yaml` at repo root is
    still discovered.

    If a custom path is provided (including nested relative paths), we do not
    change it.
    """

    p = Path(path)

    # Absolute paths, or already-existing relative paths, are used as-is.
    if p.is_absolute() or p.exists():
        return p

    # Only apply parent-search for bare filenames like "config.yaml".
    if p.parent != Path("."):
        return p

    def search_upwards(start: Path) -> Path | None:
        for parent in [start, *start.parents]:
            candidate = parent / p.name
            if candidate.exists():
                return candidate
        return None

    found = search_upwards(Path.cwd())
    if found is not None:
        return found

    # If cwd isn't inside the project (common in some notebook setups), also
    # search relative to this installed package location.
    found = search_upwards(Path(__file__).resolve().parent)
    if found is not None:
        return found

    return p
