"""Demo: MQTT subscribe (listener).

This script is intentionally beginner-friendly:
- Loads config from config.yaml (+ optional .env)
- Connects to the MQTT broker
- Subscribes to a topic and listens for messages
- Prints received messages in real-time

Run in one terminal:
    python scripts/demo/02_mqtt_subscribe.py

Then in another terminal, publish a message:
    python scripts/demo/01_config_and_mqtt.py

If imports fail, install the library first:
    pip install -e "."
"""

from __future__ import annotations

import time
from simulated_city.config import load_config
from simulated_city.mqtt import connect_mqtt, topic


def main() -> None:
    cfg = load_config()

    # Subscribe to the same topic as the publisher demo
    subscribe_topic = topic(cfg.mqtt, "events/demo")

    print("MQTT broker:", f"{cfg.mqtt.host}:{cfg.mqtt.port}", "tls=", cfg.mqtt.tls)
    print("Base topic:", cfg.mqtt.base_topic)
    print("Subscribing to:", subscribe_topic)
    print("\nWaiting for messages (press Ctrl+C to stop)...\n")

    # Connect to MQTT
    handle = connect_mqtt(cfg.mqtt, client_id_suffix="subscribe-demo", timeout_s=10.0)
    client = handle.client

    message_count = 0

    def on_connect(_client, _userdata, _connect_flags, _reason_code, _properties):
        """Callback for when the client connects to the broker."""
        print("[CONNECT] Connected to MQTT broker")

    def on_disconnect(_client, _userdata, _disconnect_flags, _reason_code, _properties):
        """Callback for when the client disconnects from the broker."""
        print("[DISCONNECT] Disconnected from MQTT broker")

    def on_message(_client, _userdata, msg):
        """Callback for when a message is received."""
        nonlocal message_count
        message_count += 1
        try:
            payload = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            payload = str(msg.payload)
        print(f"[{message_count}] Received: {msg.topic}")
        print(f"     Payload: {payload}\n")

    # Set up callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        # Start the client loop
        client.loop_start()

        # Subscribe to the topic
        client.subscribe(subscribe_topic, qos=1)

        # Keep the script running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        try:
            client.loop_stop()
        finally:
            client.disconnect()
        print("Done.")


if __name__ == "__main__":
    main()
