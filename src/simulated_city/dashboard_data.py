from __future__ import annotations

"""Shared data/parsing helpers for dashboards.

These utilities are intentionally UI-framework agnostic so they can be reused
from Streamlit scripts and Jupyter notebooks.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import queue
import ssl
import uuid
from typing import Any

import pandas as pd

from .config import MqttConfig


@dataclass(frozen=True, slots=True)
class StatusEvent:
    ts: datetime
    location_id: str
    container: str
    fill_pct: int
    timestep_index: int
    event: str


def parse_ts(value: Any) -> datetime:
    """Parse simulator/dashboard timestamps into UTC datetimes."""

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if not isinstance(value, str):
        raise ValueError("ts must be a string")

    # We emit timestamps like 2026-02-18T18:26:17.155154Z
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def series_key(location_id: str, container: str) -> str:
    return f"{location_id}.{container}"


def event_from_payload(payload: dict[str, Any]) -> StatusEvent:
    ts = parse_ts(payload["ts"])
    location_id = str(payload["location_id"])
    container = str(payload["container"])
    fill_pct = int(payload["fill_pct"])
    timestep_raw = payload.get("timestep_index", 0)
    try:
        timestep_index = int(timestep_raw)
    except (TypeError, ValueError):
        timestep_index = 0
    event = str(payload.get("event") or "status")
    return StatusEvent(
        ts=ts,
        location_id=location_id,
        container=container,
        fill_pct=fill_pct,
        timestep_index=timestep_index,
        event=event,
    )


def events_to_frame(events: list[StatusEvent]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame(columns=["ts", "series", "fill_pct", "timestep_index", "event"])

    rows = [
        {
            "ts": e.ts,
            "series": series_key(e.location_id, e.container),
            "fill_pct": e.fill_pct,
            "timestep_index": e.timestep_index,
            "event": e.event,
        }
        for e in events
    ]
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def read_jsonl_incremental(path: str, offset: int) -> tuple[list[dict[str, Any]], int]:
    """Read new JSONL lines from `path` starting at byte offset.

    Expected JSONL lines are objects that contain a dict field named "payload".
    """

    with open(path, "r", encoding="utf-8") as f:
        f.seek(offset)
        new_lines = f.readlines()
        new_offset = f.tell()

    payloads: list[dict[str, Any]] = []
    for line in new_lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and "payload" in obj and isinstance(obj["payload"], dict):
                payloads.append(obj["payload"])
        except Exception:
            continue

    return payloads, new_offset


def read_jsonl_all(path: str) -> list[dict[str, Any]]:
    """Read all payloads from a simulator JSONL log file."""

    payloads, _ = read_jsonl_incremental(path, 0)
    return payloads


def drain_queue(q: queue.Queue[dict[str, Any]], max_items: int = 5_000) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for _ in range(max_items):
        try:
            items.append(q.get_nowait())
        except queue.Empty:
            break
    return items


def start_mqtt_listener(
    mqtt_cfg: MqttConfig,
    topic_filter: str,
    *,
    client_id_suffix: str = "notebook",
) -> tuple[queue.Queue[dict[str, Any]], Any]:
    """Start an MQTT subscriber that pushes decoded JSON payloads into a queue.

    Returns (queue, client). Stop with `stop_mqtt_listener(client)`.
    """

    try:
        import paho.mqtt.client as mqtt
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError("paho-mqtt is required. Install project dependencies.") from e

    if mqtt_cfg.username is None or mqtt_cfg.password is None:
        raise RuntimeError(
            "MQTT credentials are not set. Create a .env with HIVEMQ_USERNAME and HIVEMQ_PASSWORD (or export them)."
        )

    q: queue.Queue[dict[str, Any]] = queue.Queue()

    def on_message(_client, _userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8", errors="replace")
            payload = json.loads(payload_str)
            if isinstance(payload, dict):
                q.put(payload)
        except Exception:
            # Keep subscriber robust for workshops.
            return

    client_id = f"{mqtt_cfg.client_id_prefix}-{client_id_suffix}-{uuid.uuid4().hex[:8]}"

    # Paho v2 prefers specifying the callback API version, but we keep a
    # fallback for environments with older versions.
    callback_api = getattr(mqtt, "CallbackAPIVersion", None)
    if callback_api is not None:
        try:
            client = mqtt.Client(callback_api.VERSION2, client_id=client_id)
        except Exception:
            client = mqtt.Client(client_id=client_id)
    else:
        client = mqtt.Client(client_id=client_id)

    client.on_message = on_message
    client.username_pw_set(mqtt_cfg.username, password=mqtt_cfg.password)

    if mqtt_cfg.tls:
        client.tls_set_context(ssl.create_default_context())

    client.connect(mqtt_cfg.host, mqtt_cfg.port, keepalive=mqtt_cfg.keepalive_s)
    client.subscribe(topic_filter, qos=1)

    # Run network loop in background thread.
    client.loop_start()

    return q, client


def stop_mqtt_listener(client: Any) -> None:
    """Best-effort stop for a client returned by `start_mqtt_listener`."""

    try:
        client.loop_stop()
    except Exception:
        pass
    try:
        client.disconnect()
    except Exception:
        pass
