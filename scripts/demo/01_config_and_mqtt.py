"""Demo: config + MQTT (similar to the notebook).

This script is intentionally beginner-friendly:
- Loads config from config.yaml (+ optional .env)
- Builds an example topic + JSON payload
- Optionally publishes ONE message (guarded by ENABLE_PUBLISH)

Run:
    python scripts/demo/01_config_and_mqtt.py

If imports fail, install the library first:
    pip install -e "."
"""

from __future__ import annotations

import json

from simulated_city.config import load_config
from simulated_city.mqtt import publish_json_checked, topic


# Safety switch: publishing sends a real MQTT message.
# Keep this False unless you really want to publish.
ENABLE_PUBLISH = True


def main() -> None:
    cfg = load_config()

    events_topic = topic(cfg.mqtt, "events/demo")
    payload = json.dumps({"hello": "humtek"})

    print("MQTT broker:", f"{cfg.mqtt.host}:{cfg.mqtt.port}", "tls=", cfg.mqtt.tls)
    print("Base topic:", cfg.mqtt.base_topic)
    print("Example publish topic:", events_topic)
    print("Payload:", payload)

    if not ENABLE_PUBLISH:
        print("\nSkipping publish (ENABLE_PUBLISH is False).")
        print("To publish one message: set ENABLE_PUBLISH = True in this file.")
        return

    print("\nPublishing one message...")
    result = publish_json_checked(
        cfg.mqtt,
        topic=events_topic,
        payload=payload,
        client_id_suffix="demo-script",
        wait_timeout_s=8.0,
    )
    print(result)
    if result.error:
        print("Issue:", result.error)


if __name__ == "__main__":
    main()
