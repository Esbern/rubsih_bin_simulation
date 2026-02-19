# simulated-city-template

Template project for a workshop where students learn **agent-based programming in Python** by building parts of a **simulated city / urban digital twin**.

## Quickstart (Python 3.11)

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,notebooks]"
python -m pytest
python -m jupyterlab
```

**Windows (PowerShell):**

```powershell
python3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev,notebooks]"
python -m pytest
python -m jupyterlab
```

*Note for Windows: If you get an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first.*

## Repo layout

- `docs/`: workshop notes and exercises
- `src/simulated_city/`: installable library code
- `notebooks/`: workshop notebooks
- `tests/`: small sanity tests

## MQTT (default)

- Default broker settings live in `config.yaml` (HiveMQ-style)
- MQTT helper module: `simulated_city.mqtt`
- Setup notes: `docs/mqtt.md`
- **Credentials:**
  1. Copy `.env.example` to `.env`
  2. Edit `.env` and enter your MQTT broker username and password
  - Example: `HIVEMQ_USERNAME=your_username` and `HIVEMQ_PASSWORD=your_password`

## Geo / CRS transforms (optional)

- Geo helper module: `simulated_city.geo`
- Provides CRS transforms (including WGS84 (EPSG:4326) ↔ EPSG:25832 helpers)
- Install extra: `python -m pip install -e ".[geo]"` (see `docs/setup.md`)

## First run (CLI smoke)

```bash
python -m simulated_city
```

Note: this template library intentionally ships only `simulated_city.config` and
`simulated_city.mqtt` (plus optional `simulated_city.geo`). The simulation itself is an exercise.
