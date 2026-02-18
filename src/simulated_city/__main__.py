from __future__ import annotations

import argparse

from .config import load_config
from .rubbish_sim import run_simulation


def main() -> None:
    """Small CLI smoke for the template.

    This template library intentionally does *not* ship simulation code.
    Running this module just verifies configuration loading.
    """

    parser = argparse.ArgumentParser(prog="python -m simulated_city")
    parser.add_argument("--steps", type=int, default=0, help="Number of timesteps to run (0 = smoke only)")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed override")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the simulation without publishing MQTT messages",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Optional path to write status events as JSONL (useful for dashboard playback)",
    )

    args = parser.parse_args()

    cfg = load_config()

    if args.steps and args.steps > 0:
        run_simulation(
            cfg,
            steps=args.steps,
            dry_run=bool(args.dry_run),
            seed_override=args.seed,
            log_file=args.log_file,
        )
        return

    print("simulated_city (template library)")
    print("This package includes config + MQTT helpers, plus an example rubbish-bin simulation.")
    print()
    print(f"MQTT broker: {cfg.mqtt.host}:{cfg.mqtt.port} tls={cfg.mqtt.tls}")
    print(f"MQTT base topic: {cfg.mqtt.base_topic}")
    print()
    print("Next:")
    print("- See docs/mqtt.md for broker setup")
    print("- Run the simulation: python -m simulated_city --steps 200")


if __name__ == "__main__":
    main()
