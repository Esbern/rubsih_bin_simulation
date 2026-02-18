from __future__ import annotations

"""Rubbish-bin filling simulation.

This module implements a small, beginner-friendly simulation matching the
behavior described in README.md:

- Multiple locations (lat/lon)
- 3 containers per location (left/center/right)
- Discrete timesteps
- Stochastic arrivals and deposits
- MQTT status messages when a container crosses a fill boundary (e.g. every 10%)

The implementation prioritizes clarity and testability over performance.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import io
import json
import random
import time
from typing import Literal

from .config import AppConfig, MqttConfig, SimulationConfig, SimulationLocationConfig
from .mqtt import MqttClientHandle, connect_mqtt, topic


ContainerName = Literal["left", "center", "right"]


@dataclass(frozen=True, slots=True)
class ContainerState:
    """Immutable state of a single container."""

    fill_pct: int

    @property
    def is_full(self) -> bool:
        return self.fill_pct >= 100


@dataclass(frozen=True, slots=True)
class LocationState:
    """Immutable state of a location (3 containers)."""

    location_id: str
    lat: float
    lon: float
    left: ContainerState
    center: ContainerState
    right: ContainerState


@dataclass(frozen=True, slots=True)
class DepositResult:
    """Result of attempting a deposit at a location."""

    deposited: bool
    container: ContainerName | None
    old_fill_pct: int | None
    new_fill_pct: int | None


class StatusPublisher:
    """A small interface for publishing status messages."""

    def publish_status(
        self,
        *,
        ts: datetime,
        location: LocationState,
        container: ContainerName,
        fill_pct: int,
        timestep_index: int,
        event: str = "status",
    ) -> None:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class NoopStatusPublisher(StatusPublisher):
    def publish_status(
        self,
        *,
        ts: datetime,
        location: LocationState,
        container: ContainerName,
        fill_pct: int,
        timestep_index: int,
        event: str = "status",
    ) -> None:
        return


@dataclass(frozen=True, slots=True)
class StdoutStatusPublisher(StatusPublisher):
    """Dry-run publisher that prints what would be sent to MQTT.

    This is useful for debugging topic/payload formatting without needing an
    MQTT broker.
    """

    mqtt_cfg: MqttConfig

    def publish_status(
        self,
        *,
        ts: datetime,
        location: LocationState,
        container: ContainerName,
        fill_pct: int,
        timestep_index: int,
        event: str = "status",
    ) -> None:
        payload = make_status_payload(
            ts=ts,
            location=location,
            container=container,
            fill_pct=fill_pct,
            timestep_index=timestep_index,
            event=event,
        )
        suffix = f"bins/{location.location_id}/{container}/status"
        full_topic = topic(self.mqtt_cfg, suffix)
        print(f"[DRY-RUN] topic={full_topic} payload={payload}")


@dataclass(frozen=True, slots=True)
class JsonlFileStatusPublisher(StatusPublisher):
    """Publisher that writes status events to a JSONL file.

    Each line is a JSON object:
    {"topic": "...", "payload": { ... }}
    """

    mqtt_cfg: MqttConfig
    fp: io.TextIOBase

    def publish_status(
        self,
        *,
        ts: datetime,
        location: LocationState,
        container: ContainerName,
        fill_pct: int,
        timestep_index: int,
        event: str = "status",
    ) -> None:
        payload_str = make_status_payload(
            ts=ts,
            location=location,
            container=container,
            fill_pct=fill_pct,
            timestep_index=timestep_index,
            event=event,
        )
        suffix = f"bins/{location.location_id}/{container}/status"
        full_topic = topic(self.mqtt_cfg, suffix)

        line_obj = {
            "topic": full_topic,
            "payload": json.loads(payload_str),
        }
        self.fp.write(json.dumps(line_obj, ensure_ascii=False) + "\n")
        self.fp.flush()


@dataclass(frozen=True, slots=True)
class TeeStatusPublisher(StatusPublisher):
    """Fan-out publisher that forwards to multiple publishers."""

    publishers: tuple[StatusPublisher, ...]

    def publish_status(
        self,
        *,
        ts: datetime,
        location: LocationState,
        container: ContainerName,
        fill_pct: int,
        timestep_index: int,
        event: str = "status",
    ) -> None:
        for p in self.publishers:
            p.publish_status(
                ts=ts,
                location=location,
                container=container,
                fill_pct=fill_pct,
                timestep_index=timestep_index,
                event=event,
            )


@dataclass(frozen=True, slots=True)
class MqttStatusPublisher(StatusPublisher):
    """Publish retained status messages over MQTT."""

    handle: MqttClientHandle
    mqtt_cfg: MqttConfig

    def publish_status(
        self,
        *,
        ts: datetime,
        location: LocationState,
        container: ContainerName,
        fill_pct: int,
        timestep_index: int,
        event: str = "status",
    ) -> None:
        payload = make_status_payload(
            ts=ts,
            location=location,
            container=container,
            fill_pct=fill_pct,
            timestep_index=timestep_index,
            event=event,
        )
        suffix = f"bins/{location.location_id}/{container}/status"
        self.handle.publish_json(topic(self.mqtt_cfg, suffix), payload, qos=1, retain=True)


def make_status_payload(
    *,
    ts: datetime,
    location: LocationState,
    container: ContainerName,
    fill_pct: int,
    timestep_index: int,
    event: str = "status",
) -> str:
    """Create the JSON payload string for a container status message."""

    data = {
        "ts": ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "location_id": location.location_id,
        "lat": location.lat,
        "lon": location.lon,
        "container": container,
        "fill_pct": int(fill_pct),
        "timestep_index": int(timestep_index),
        "event": str(event),
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def boundaries_crossed(old_fill_pct: int, new_fill_pct: int, *, boundary_pct: int) -> list[int]:
    """Return boundary values crossed when fill increases.

    Example: old=19, new=31, boundary=10 -> [20, 30]

    Notes
    - Only upward crossings are reported (this simulation doesn't decrease fill).
    - Returned boundaries are the boundary values (10, 20, 30, ...).
    """

    if boundary_pct <= 0:
        raise ValueError("boundary_pct must be > 0")

    old_bucket = old_fill_pct // boundary_pct
    new_bucket = new_fill_pct // boundary_pct

    if new_bucket <= old_bucket:
        return []

    return [i * boundary_pct for i in range(old_bucket + 1, new_bucket + 1)]


def _pick_preferred_container(rng: random.Random) -> ContainerName:
    """Pick preferred container using the 50/25/25 rule."""

    roll = rng.random()
    if roll < 0.25:
        return "left"
    if roll < 0.75:
        return "center"
    return "right"


def choose_container(
    *,
    rng: random.Random,
    left: ContainerState,
    center: ContainerState,
    right: ContainerState,
) -> ContainerName | None:
    """Choose a container with fallback if the preferred one is full."""

    preferred = _pick_preferred_container(rng)

    containers: dict[ContainerName, ContainerState] = {
        "left": left,
        "center": center,
        "right": right,
    }

    if not containers[preferred].is_full:
        return preferred

    available = [name for name, state in containers.items() if not state.is_full]
    if not available:
        return None

    return rng.choice(available)


def _apply_deposit(container: ContainerState, *, delta_pct: int) -> tuple[ContainerState, int, int]:
    old_fill = int(container.fill_pct)
    new_fill = min(100, old_fill + int(delta_pct))
    return ContainerState(fill_pct=new_fill), old_fill, new_fill


def step_location(
    *,
    rng: random.Random,
    sim_cfg: SimulationConfig,
    location: LocationState,
) -> tuple[LocationState, DepositResult]:
    """Advance one timestep for a single location."""

    arrived = rng.random() < sim_cfg.arrival_prob
    if not arrived:
        return location, DepositResult(deposited=False, container=None, old_fill_pct=None, new_fill_pct=None)

    chosen = choose_container(rng=rng, left=location.left, center=location.center, right=location.right)
    if chosen is None:
        return location, DepositResult(deposited=False, container=None, old_fill_pct=None, new_fill_pct=None)

    if chosen == "left":
        new_state, old_fill, new_fill = _apply_deposit(location.left, delta_pct=sim_cfg.bag_fill_delta_pct)
        updated = LocationState(
            location_id=location.location_id,
            lat=location.lat,
            lon=location.lon,
            left=new_state,
            center=location.center,
            right=location.right,
        )
        return updated, DepositResult(deposited=True, container="left", old_fill_pct=old_fill, new_fill_pct=new_fill)

    if chosen == "center":
        new_state, old_fill, new_fill = _apply_deposit(location.center, delta_pct=sim_cfg.bag_fill_delta_pct)
        updated = LocationState(
            location_id=location.location_id,
            lat=location.lat,
            lon=location.lon,
            left=location.left,
            center=new_state,
            right=location.right,
        )
        return updated, DepositResult(deposited=True, container="center", old_fill_pct=old_fill, new_fill_pct=new_fill)

    new_state, old_fill, new_fill = _apply_deposit(location.right, delta_pct=sim_cfg.bag_fill_delta_pct)
    updated = LocationState(
        location_id=location.location_id,
        lat=location.lat,
        lon=location.lon,
        left=location.left,
        center=location.center,
        right=new_state,
    )
    return updated, DepositResult(deposited=True, container="right", old_fill_pct=old_fill, new_fill_pct=new_fill)


def _initial_location_state(loc: SimulationLocationConfig) -> LocationState:
    return LocationState(
        location_id=loc.location_id,
        lat=loc.lat,
        lon=loc.lon,
        left=ContainerState(fill_pct=0),
        center=ContainerState(fill_pct=0),
        right=ContainerState(fill_pct=0),
    )


def run_simulation(
    cfg: AppConfig,
    *,
    steps: int,
    dry_run: bool = False,
    seed_override: int | None = None,
    log_file: str | None = None,
) -> None:
    """Run the rubbish-bin simulation for a given number of timesteps."""

    if steps <= 0:
        raise ValueError("steps must be > 0")

    sim_cfg = cfg.simulation
    if sim_cfg is None or not sim_cfg.locations:
        raise ValueError("No simulation configured. Add a 'simulation.locations' section in config.yaml.")

    seed = seed_override if seed_override is not None else sim_cfg.seed
    rng = random.Random(seed)

    locations = [_initial_location_state(loc) for loc in sim_cfg.locations]

    publisher: StatusPublisher
    client = None
    log_fp: io.TextIOWrapper | None = None

    publishers: list[StatusPublisher] = []
    if log_file:
        # Overwrite by default so a single log file corresponds to one run.
        # This avoids confusing dashboards with apparent fill decreases caused
        # by appended runs.
        log_fp = open(log_file, "w", encoding="utf-8")
        publishers.append(JsonlFileStatusPublisher(mqtt_cfg=cfg.mqtt, fp=log_fp))

    if dry_run:
        publishers.append(StdoutStatusPublisher(mqtt_cfg=cfg.mqtt))
        publisher = TeeStatusPublisher(publishers=tuple(publishers)) if len(publishers) > 1 else publishers[0]
    else:
        handle = connect_mqtt(cfg.mqtt, client_id_suffix="rubbish-sim")
        client = handle.client
        client.loop_start()
        publishers.append(MqttStatusPublisher(handle=handle, mqtt_cfg=cfg.mqtt))
        publisher = TeeStatusPublisher(publishers=tuple(publishers)) if len(publishers) > 1 else publishers[0]

    try:
        start_ts = sim_cfg.start_time or datetime.now(timezone.utc)

        # Publish an initial status for every container so dashboards can show
        # all bins immediately (aligned at the same start timestamp).
        for loc_state in locations:
            for container_name in ("left", "center", "right"):
                publisher.publish_status(
                    ts=start_ts,
                    location=loc_state,
                    container=container_name,
                    fill_pct=getattr(loc_state, container_name).fill_pct,
                    timestep_index=-1,
                    event="init",
                )

        for timestep_index in range(steps):
            ts = start_ts + timedelta(minutes=sim_cfg.timestep_minutes * timestep_index)

            for i, loc_state in enumerate(locations):
                updated, deposit = step_location(rng=rng, sim_cfg=sim_cfg, location=loc_state)
                locations[i] = updated

                if not deposit.deposited:
                    continue

                assert deposit.container is not None
                assert deposit.old_fill_pct is not None
                assert deposit.new_fill_pct is not None

                if sim_cfg.publish_every_deposit:
                    publisher.publish_status(
                        ts=ts,
                        location=updated,
                        container=deposit.container,
                        fill_pct=deposit.new_fill_pct,
                        timestep_index=timestep_index,
                        event="status",
                    )
                else:
                    for _boundary in boundaries_crossed(
                        deposit.old_fill_pct,
                        deposit.new_fill_pct,
                        boundary_pct=sim_cfg.status_boundary_pct,
                    ):
                        publisher.publish_status(
                            ts=ts,
                            location=updated,
                            container=deposit.container,
                            fill_pct=deposit.new_fill_pct,
                            timestep_index=timestep_index,
                            event="status",
                        )

            # Optional wall-clock delay for demos / MQTT dashboard testing.
            if sim_cfg.step_delay_s > 0:
                time.sleep(sim_cfg.step_delay_s)
    finally:
        if log_fp is not None:
            log_fp.close()
        if client is not None:
            try:
                client.loop_stop()
            finally:
                client.disconnect()
