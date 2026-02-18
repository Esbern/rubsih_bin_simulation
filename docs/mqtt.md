# MQTT

This template includes **paho-mqtt** by default and ships with a committed `config.yaml` that points at a HiveMQ-style broker configuration.

This document covers everything in `simulated_city.mqtt`:

- `connect_mqtt(...)`
- `topic(...)`
- `publish_json_checked(...)`
- `MqttClientHandle` and `PublishCheckResult`

## Configure HiveMQ Cloud

1. Edit `config.yaml`:
   - Set `mqtt.host` to your HiveMQ cluster host (example: `xxxxxx.s1.eu.hivemq.cloud`)
   - Keep `mqtt.port: 8883` and `mqtt.tls: true`

2. Store credentials in a local `.env` file:

```bash
cp .env.example .env
# edit .env and set:
# HIVEMQ_USERNAME=...
# HIVEMQ_PASSWORD=...
```

## Connect from Python

```python
from simulated_city.config import load_config
from simulated_city.mqtt import connect_mqtt, topic

cfg = load_config().mqtt
handle = connect_mqtt(cfg, client_id_suffix="demo")
handle.client.loop_start()

handle.publish_json(topic(cfg, "metrics"), '{"step": 1, "agents": 25}')
```

Notes:

- `connect_mqtt(...)` returns a `MqttClientHandle` which wraps the underlying paho client.
- You must start the network loop yourself (`handle.client.loop_start()` or `loop_forever()`).


## Functions

### `topic(cfg, suffix) -> str`

Builds a full MQTT topic using the configured base topic.

Example:

```python
from simulated_city.config import load_config
from simulated_city.mqtt import topic

mqtt_cfg = load_config().mqtt
print(topic(mqtt_cfg, "events/demo"))
```


### `connect_mqtt(cfg, client_id_suffix=None, timeout_s=10.0) -> MqttClientHandle`

Creates an MQTT client and connects to the broker.

Example:

```python
from simulated_city.config import load_config
from simulated_city.mqtt import connect_mqtt

mqtt_cfg = load_config().mqtt
handle = connect_mqtt(mqtt_cfg, client_id_suffix="demo")
handle.client.loop_start()
```


### `publish_json_checked(...) -> PublishCheckResult`

Workshop-friendly helper that:

1. connects
2. optionally subscribes to the same topic (self-check)
3. publishes the message
4. waits briefly for acks/messages
5. disconnects

It is designed for notebooks when you want a simple “did it work?” signal.

Example:

```python
import json

from simulated_city.config import load_config
from simulated_city.mqtt import publish_json_checked, topic

cfg = load_config().mqtt
events_topic = topic(cfg, "events/demo")
payload = json.dumps({"hello": "humtek"})

result = publish_json_checked(cfg, topic=events_topic, payload=payload, client_id_suffix="notebook")
print(result)
if result.error:
   print("Issue:", result.error)
```


## Classes

### `MqttClientHandle`

Wrapper that exposes the underlying paho client as `.client`.

#### `publish_json(topic, payload, qos=0, retain=False) -> None`

Convenience method around paho’s `publish()`.

Example:

```python
from simulated_city.config import load_config
from simulated_city.mqtt import connect_mqtt, topic

cfg = load_config().mqtt
handle = connect_mqtt(cfg, client_id_suffix="demo")
handle.client.loop_start()

handle.publish_json(topic(cfg, "metrics"), '{"agents": 25}')
```


### `PublishCheckResult`

Returned by `publish_json_checked(...)`.

Useful fields:

- `published`: did we see `on_publish`
- `received`: did we receive the message back (only if `self_subscribe=True`)
- `received_payload`: what we received (string)
- `error`: a short human-readable error message (or `None`)

## Using other brokers

Projects can switch brokers by editing `config.yaml` (host/port/tls) or by loading a different config file.
