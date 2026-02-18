## Plan: Implement Rubbish Bin Filling Simulation + MQTT Status

TL;DR: add a small simulation engine (locations + 3 containers each + timestep loop), extend YAML config to describe locations/probabilities, and publish MQTT “status” messages whenever a container crosses a 10% fill boundary. Reuse the existing config loader and MQTT helpers, and add a CLI entry point to run N steps deterministically (seeded RNG) for dashboard/testing.

Remember to write clean, modular code with clear separation of concerns (config parsing, simulation logic, MQTT publishing) and to document your design decisions and assumptions in the README. This will make it easier to iterate on the simulation rules and add realism improvements later without needing to refactor heavily. also ensure that the code is testable (e.g., by injecting a seeded RNG) and that the README clearly describes the intended behavior and MQTT outputs for future dashboard integration. Finaly the code must prioritize readability over efficiency, since the simulation is not expected to handle large scale or real-time loads at this stage, but should be structured in a way that allows for easy extension (e.g., adding emptying logic, more complex arrival patterns, or multiple locations) without needing to rewrite the core loop.

**Steps**
1. Define simulation config + data models
   - Extend `src/simulated_city/config.py` to parse a new `simulation:` section into dataclasses (keep `frozen=True, slots=True` style).
   - Add dataclasses (new module): `src/simulated_city/rubbish_sim.py` (or split into `models.py`/`engine.py` if you prefer)
     - `LocationState`: `location_id`, `lat`, `lon`, containers `{left, center, right}`
     - `ContainerState`: `fill_pct` and derived `is_full`
     - `SimulationConfig`: `timestep_minutes=15`, `arrival_prob=0.25`, `bag_fill_delta_pct=2`, optional `seed`, `status_boundary_pct=10`
2. Add YAML schema to config.yaml (no secrets)
   - Update `config.yaml` with something like:
     - `simulation.locations`: list of `{id, lat, lon}`
     - optional overrides: `arrival_prob`, `bag_fill_delta_pct`, `timestep_minutes`, `seed`
   - Keep MQTT config unchanged (already works).
3. Implement the core step loop (no emptying yet)
   - In `src/simulated_city/rubbish_sim.py` implement `run_simulation(cfg: AppConfig, steps: int)`.
   - Per timestep per location:
     - roll arrival with `random.Random(seed)` for reproducibility
     - choose container with 50/25/25 weighting; if chosen full, select among non-full; if all full, emit an “unable_to_deposit” event (at least log + optional MQTT)
     - apply deposit: `fill_pct = min(100, fill_pct + 2)`
4. Implement “crosses 10% boundary” detection
   - Track `old_bucket = old_fill_pct // 10` and `new_bucket = new_fill_pct // 10`.
   - If `new_bucket > old_bucket`, publish a status message.
   - Decision to document in code/README: publish **one** status message per crossing event (with current `fill_pct`), or publish **one per boundary** if a larger bag ever skips multiple buckets (I’d implement “one per boundary crossed” to match the wording).
5. MQTT publishing (persistent connection)
   - Reuse `src/simulated_city/mqtt.py`:
     - connect once via `connect_mqtt`, call `client.loop_start()`, publish repeatedly via `MqttClientHandle.publish_json`
   - Implement topic builder consistent with README:
     - `topic(cfg.mqtt, f"bins/{location_id}/{container}/status")`
   - Payload: JSON string with fields from README (`ts`, `location_id`, `lat`, `lon`, `container`, `fill_pct`, `timestep_index`, `event`)
6. CLI entry point
   - Update `src/simulated_city/__main__.py` to optionally run the simulation when `simulation.locations` exists (or add a new module `simulated_city.rubbish_cli` and call it from `__main__`).
   - Support flags: `--steps`, `--seed` (override config), maybe `--dry-run` (no MQTT) if you want quick local runs.
7. Tests (fast, deterministic)
   - Add tests for:
     - config parsing of `simulation.locations` (new tests near `tests/test_config.py`)
     - bucket-crossing logic (pure function: given old/new fill, does it publish?)
     - container selection fallback when full (deterministic RNG with forced full containers)
   - Keep MQTT out of unit tests (test payload/topic generation as strings).
8. Docs touch-ups
   - Ensure README matches final topic/payload choices (also: there’s a stray `◊` in the “Containers” heading in `README.md` you’ll want to remove).
   - Optionally add a short “Simulation config example” section to README once YAML is finalized.

**Verification**
- `pytest`
- Manual run: `python -m simulated_city --steps 200` and observe MQTT retained status updates per container at each 10% boundary (e.g., 10, 20, …).
- Optional: run the existing MQTT subscribe demo in `scripts/demo/02_mqtt_subscribe.py` to confirm messages arrive.

**Decisions**
- Use seeded RNG (`seed` in config + CLI override) so runs are reproducible.
- Publish status on boundary crossings using integer buckets (`fill_pct // 10`).
- Keep emptying/collection out of scope for the first implementation, but structure state so it can be added later.
