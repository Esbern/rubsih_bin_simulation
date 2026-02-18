from __future__ import annotations

from dataclasses import dataclass
import socket
import ssl
import time
import threading
from typing import TYPE_CHECKING

from .config import MqttConfig

if TYPE_CHECKING:
    import paho.mqtt.client as mqtt


@dataclass(frozen=True, slots=True)
class MqttClientHandle:
    client: "mqtt.Client"

    def publish_json(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
        # Keep it string-based by default to avoid forcing a JSON dependency.
        result = self.client.publish(topic, payload=payload, qos=qos, retain=retain)
        result.wait_for_publish()


def connect_mqtt(cfg: MqttConfig, *, client_id_suffix: str | None = None, timeout_s: float = 10.0) -> MqttClientHandle:
    """Create and connect an MQTT client using configuration.

    Notes:
    - This function does not run a loop for you; call `client.loop_start()` or `client.loop_forever()`.
    - Credentials are optional; for HiveMQ Cloud you'll typically set env vars.
    """

    try:
        import paho.mqtt.client as mqtt
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "paho-mqtt is required to use simulated_city.mqtt. "
            "Install dependencies (e.g. `pip install -e .`) and try again."
        ) from e

    client_id = _make_client_id(cfg.client_id_prefix, client_id_suffix)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)

    if cfg.username is not None:
        client.username_pw_set(cfg.username, password=cfg.password)

    if cfg.tls:
        context = ssl.create_default_context()
        client.tls_set_context(context)

    # Connect (TCP) with a simple timeout.
    started = time.time()
    last_err: Exception | None = None
    while time.time() - started < timeout_s:
        try:
            client.connect(cfg.host, cfg.port, keepalive=cfg.keepalive_s)
            break
        except (OSError, socket.gaierror, ssl.SSLError) as e:
            last_err = e
            time.sleep(0.25)

    if time.time() - started >= timeout_s:
        raise TimeoutError(f"Failed to connect to MQTT broker {cfg.host}:{cfg.port} within {timeout_s}s") from last_err

    # Verify MQTT CONNACK (this is where auth/ACL errors show up). The paho
    # client won't process CONNACK until a network loop is running.
    connected = threading.Event()
    connect_err: list[str] = []

    def on_connect(_client, _userdata, _connect_flags, reason_code, _properties):
        try:
            code = getattr(reason_code, "value", reason_code)
            code_int = int(code)
        except Exception:
            code_int = -1

        if code_int != 0:
            connect_err.append(f"CONNACK reason_code={reason_code}")
        connected.set()

    client.on_connect = on_connect
    client.loop_start()
    try:
        if not connected.wait(timeout_s):
            raise TimeoutError(f"Timed out waiting for MQTT CONNACK from {cfg.host}:{cfg.port}")
        if connect_err:
            msg = (
                "MQTT connection was rejected by the broker (likely auth/ACL). "
                f"Details: {connect_err[0]}. "
                "If you're using HiveMQ Cloud, ensure HIVEMQ_USERNAME and HIVEMQ_PASSWORD are set (e.g. in .env)."
            )
            raise ConnectionError(msg)
    finally:
        client.loop_stop()

    return MqttClientHandle(client=client)


@dataclass(frozen=True, slots=True)
class PublishCheckResult:
    topic: str
    qos: int
    retain: bool
    published: bool
    received: bool
    received_payload: str | None
    error: str | None


def publish_json_checked(
    cfg: MqttConfig,
    *,
    topic: str,
    payload: str,
    qos: int = 1,
    retain: bool = True,
    client_id_suffix: str | None = None,
    connect_timeout_s: float = 10.0,
    wait_timeout_s: float = 5.0,
    self_subscribe: bool = True,
) -> PublishCheckResult:
    """Publish a JSON string and optionally verify delivery by self-subscribing.

    This helper is designed for notebooks and workshops:
    - Connects
    - (Optionally) subscribes to the same topic
    - Publishes with QoS (default 1)
    - Waits briefly for on_publish and on_message
    - Disconnects cleanly

    Notes
    - `retain=True` can make messages visible in broker UIs even when no
      subscriber is currently listening.
    - `received=True` requires `self_subscribe=True` and that the broker allows
      the client to subscribe to that topic.
    """

    handle = connect_mqtt(cfg, client_id_suffix=client_id_suffix, timeout_s=connect_timeout_s)
    client = handle.client

    published = threading.Event()
    received = threading.Event()
    received_payload: str | None = None

    def on_publish(*args, **kwargs):
        published.set()

    def on_message(_client, _userdata, msg):
        nonlocal received_payload
        try:
            received_payload = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            received_payload = str(msg.payload)
        received.set()

    client.on_publish = on_publish
    client.on_message = on_message

    try:
        client.loop_start()

        if self_subscribe:
            client.subscribe(topic, qos=qos)
            time.sleep(0.25)

        info = client.publish(topic, payload=payload, qos=qos, retain=retain)
        # Ensure the message is actually sent (and acked for QoS>0).
        info.wait_for_publish(timeout=wait_timeout_s)

        pub_ok = published.wait(wait_timeout_s)
        recv_ok = received.wait(wait_timeout_s) if self_subscribe else False

        err: str | None = None
        if not pub_ok:
            err = "Timed out waiting for publish acknowledgement (on_publish)."
        elif self_subscribe and not recv_ok:
            err = "Published but did not receive message back. Check ACLs/topic/subscription."

        return PublishCheckResult(
            topic=topic,
            qos=qos,
            retain=retain,
            published=pub_ok,
            received=recv_ok,
            received_payload=received_payload,
            error=err,
        )
    finally:
        try:
            client.loop_stop()
        finally:
            client.disconnect()


def topic(cfg: MqttConfig, suffix: str) -> str:
    suffix = suffix.lstrip("/")
    return f"{cfg.base_topic}/{suffix}" if suffix else cfg.base_topic


def _make_client_id(prefix: str, suffix: str | None) -> str:
    safe_prefix = prefix.strip() or "simcity"
    if suffix:
        return f"{safe_prefix}-{suffix}"
    return safe_prefix
