"""MQTT smoke test: publish + self-receive a bin status message.

This verifies:
- config.yaml + .env credentials load
- broker connectivity + auth
- topic ACLs (publish + subscribe)
- payload is JSON and matches the bin status schema used by the simulator/dashboard

Run:
    ./.venv/bin/python scripts/demo/03_mqtt_smoke_test_bins_status.py

Tip: In another terminal you can watch all bin status traffic:
    ./.venv/bin/python scripts/demo/02_mqtt_subscribe.py --bins
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json

from simulated_city.config import load_config
from simulated_city.mqtt import publish_json_checked


def main() -> None:
    parser = argparse.ArgumentParser(description="MQTT smoke test for bin status topics")
    parser.add_argument("--location-id", default="smoke_test", help="location_id to publish under")
    parser.add_argument("--container", default="left", choices=["left", "center", "right"], help="container name")
    parser.add_argument("--fill-pct", type=int, default=42, help="fill percentage to publish (0-100)")
    parser.add_argument("--retain", action=argparse.BooleanOptionalAction, default=True, help="publish retained message")
    args = parser.parse_args()

    cfg = load_config().mqtt

    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    topic = f"{cfg.base_topic}/bins/{args.location_id}/{args.container}/status"

    payload_obj = {
        "ts": ts,
        "location_id": str(args.location_id),
        "lat": 55.67597,
        "lon": 12.56984,
        "container": str(args.container),
        "fill_pct": int(max(0, min(100, args.fill_pct))),
        "timestep_index": -999,
        "event": "status",
    }
    payload = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":"))

    print("MQTT broker:", f"{cfg.host}:{cfg.port}", "tls=", cfg.tls)
    print("Base topic:", cfg.base_topic)
    print("Publish topic:", topic)

    result = publish_json_checked(
        cfg,
        topic=topic,
        payload=payload,
        qos=1,
        retain=bool(args.retain),
        client_id_suffix="smoke-test",
        wait_timeout_s=8.0,
        self_subscribe=True,
    )

    print(result)
    if result.error:
        raise SystemExit(f"Smoke test failed: {result.error}")

    if result.received_payload is None:
        raise SystemExit("Smoke test failed: no payload received")

    print("Smoke test OK: published and received one message.")


if __name__ == "__main__":
    main()
