# Configuration (`simulated_city.config`)

This module loads workshop configuration from:

- `config.yaml` (committed defaults, safe to share)
- optional `.env` (gitignored, for secrets like broker credentials)

It returns a single `AppConfig` object that contains `MqttConfig`.


## Install

The base install already includes config support:

```bash
pip install -e "."
```


## Data classes

### `MqttConfig`

Holds broker and topic settings.

Typical fields:

- `host`, `port`, `tls`
- `username`, `password` (usually loaded from environment variables)
- `client_id_prefix`, `keepalive_s`, `base_topic`


### `AppConfig`

Top-level config wrapper. Currently contains:

- `mqtt: MqttConfig`


## Functions

### `load_config(path="config.yaml") -> AppConfig`

Loads configuration, applying these rules:

1. Load `.env` from the current working directory if present.
2. Find `config.yaml`:
   - if `path` exists (or is absolute), use it
   - if `path` is a bare filename like `config.yaml`, search parent directories
     so notebooks in `notebooks/` still find the repo-root `config.yaml`
3. Read `mqtt.*` settings from YAML.
4. Optionally read credentials from environment variables named in YAML:
   - `mqtt.username_env`
   - `mqtt.password_env`

Example:

```python
from simulated_city.config import load_config

cfg = load_config()
print(cfg.mqtt.host, cfg.mqtt.port, cfg.mqtt.tls)
print("base topic:", cfg.mqtt.base_topic)
```


## Internal helpers (advanced)

These are used by `load_config()` and normally don’t need to be called directly:

- `_load_yaml_dict(path) -> dict`: reads a YAML mapping (or returns `{}`)
- `_resolve_default_config_path(path) -> Path`: notebook-friendly path resolution
