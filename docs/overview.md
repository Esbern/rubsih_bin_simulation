# Simulated City (Workshop Template)

This template is for a workshop where students learn **agent-based programming in Python** by building pieces of a simple "simulated city"—a lightweight starting point for an **urban digital twin**.

The goal is to keep the code:

- Small enough to read in one sitting
- Modular enough to extend (agents, places, sensors, movement rules)
- Practical for notebook-driven exploration



## Repo overview

- `src/simulated_city/`: the library students import
- `notebooks/`: workshop notebooks
- `docs/`: workshop handouts and exercises
- `tests/`: small sanity checks

## Library modules

- `simulated_city.config`: load settings from `config.yaml` + optional `.env`
- `simulated_city.mqtt`: build topics, connect, and publish MQTT messages
- `simulated_city.geo` (optional): CRS transforms for real-world coordinates
  - Enable with: `pip install -e ".[geo]"`
  - Includes beginner-friendly helpers like `wgs2utm(...)` / `utm2wgs(...)`


## Docs index

Module docs:

- `docs/config.md` — `simulated_city.config`
- `docs/mqtt.md` — `simulated_city.mqtt`
- `docs/geo.md` — `simulated_city.geo` (optional)
- `docs/__init__.md` — top-level package API (`simulated_city`)
- `docs/__main__.md` — CLI smoke (`python -m simulated_city`)

Workshop docs:

- `docs/setup.md` — environment setup + optional extras
- `docs/demos.md` — script demos (same ideas as the notebook)
- `docs/exercises.md` — student exercises (build the simulation)
