# Package API (`simulated_city`)

The `simulated_city` package is a small helper library used by workshop notebooks.

It intentionally keeps only workshop-agnostic building blocks:

- Configuration loading (`simulated_city.config`)
- MQTT helpers (`simulated_city.mqtt`)
- Optional CRS transforms (`simulated_city.geo`)


## Import patterns

You can import from submodules:

```python
from simulated_city.config import load_config
from simulated_city.mqtt import topic, publish_json_checked
```

Or import convenience re-exports from the package root:

```python
from simulated_city import load_config, topic, publish_json_checked
```


## Re-exported names

The package root re-exports these names for convenience:

- Config: `AppConfig`, `MqttConfig`, `load_config`
- Geo: `EPSG_3857`, `EPSG_25832`, `transform_xy`, `transform_many`,
  `webmercator_to_epsg25832`, `epsg25832_to_webmercator`, `wgs2utm`, `utm2wgs`
- MQTT: `MqttClientHandle`, `PublishCheckResult`, `connect_mqtt`, `publish_json_checked`, `topic`

Tip: for detailed documentation and more examples, see:

- `docs/config.md`
- `docs/mqtt.md`
- `docs/geo.md`
