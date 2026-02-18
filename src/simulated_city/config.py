from __future__ import annotations

from dataclasses import dataclass, field
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


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    # Load a local .env if present (it is gitignored by default).
    # This makes workshop setup easier while keeping secrets out of git.
    load_dotenv(override=False)

    resolved_path = _resolve_default_config_path(path)
    data = _load_yaml_dict(resolved_path)
    mqtt = data.get("mqtt") or {}

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
        )
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
