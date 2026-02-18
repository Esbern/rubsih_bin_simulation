from __future__ import annotations

from .config import load_config


def main() -> None:
    """Small CLI smoke for the template.

    This template library intentionally does *not* ship simulation code.
    Running this module just verifies configuration loading.
    """

    cfg = load_config()

    print("simulated_city (template library)")
    print("This package only includes config + MQTT helpers.")
    print()
    print(f"MQTT broker: {cfg.mqtt.host}:{cfg.mqtt.port} tls={cfg.mqtt.tls}")
    print(f"MQTT base topic: {cfg.mqtt.base_topic}")
    print()
    print("Next:")
    print("- See docs/mqtt.md for broker setup")
    print("- See docs/exercises.md to build the simulation")


if __name__ == "__main__":
    main()
