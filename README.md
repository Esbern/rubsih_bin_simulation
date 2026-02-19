# Rubbish Bin Simulation (Copenhagen)

This project simulates **household waste containers** being filled over time at one or more locations in Copenhagen.

Collection/emptying is **out of scope for now** (not implemented yet). The short-term goal is to publish container status so a dashboard can monitor fill levels.

## Simulation model (current spec)

### Locations

- The simulation supports **multiple locations**.
- Each location has a user-provided coordinate: **latitude/longitude (WGS84 / EPSG:4326)**.

### Containers

Each location has three containers:

- `left`
- `center`
- `right`

Container state is modeled as:

- `fill_pct` (0–100)
- A container is **full** when `fill_pct == 100`.

### Time

- The simulation advances in discrete steps.
- **One timestep = 15 minutes.**

### Arrivals and deposits

For each timestep:

- With probability **25%**, a person arrives to deposit a waste bag.
- Each deposited bag increases the chosen container by **2 percentage points** (`+2 fill_pct`).

### Choice of container

When a person arrives:

- They choose `center` with probability **50%**.
- They choose `left` with probability **25%**.
- They choose `right` with probability **25%**.

If the chosen container is full, the person chooses among the remaining non-full containers.

If **all** containers at that location are full, the simulation should record an “unable to deposit” event (exact behavior TBD).

## MQTT outputs (target)

The code should use the existing MQTT utilities in `src/simulated_city/mqtt.py`.

Goal: publish a **status update each time a container crosses a 10% boundary** ("status for each 10 pct").

Suggested payload fields:

- `ts`: ISO-8601 timestamp
- `location_id`: stable identifier for the location
- `lat`, `lon`: location coordinate
- `container`: `left|center|right`
- `fill_pct`: integer 0–100
- `timestep_index`: integer step counter
- `event`: e.g. `status` or `deposit`

Suggested topic convention (can be adjusted later):

- `simulated-city/bins/{location_id}/{container}/status`

## Dashboard

The project includes a small Streamlit dashboard that can show fill graphs and alerts.

### Install dashboard dependencies

```bash
python -m pip install -e ".[dashboard]"
```

### Run dashboard (log file mode)

Generate a JSONL log file (the file is overwritten per run):

```bash
python -m simulated_city --steps 500 --dry-run --log-file sim_status.jsonl
```

Run the dashboard:

```bash
streamlit run scripts/dashboard/bin_dashboard.py
```

Then select **Log file** in the sidebar and set the path to `sim_status.jsonl`.

Tip: if you want more frequent points for graphs, set `simulation.publish_every_deposit: true` in `config.yaml`.

### Run dashboard (MQTT mode)

1. Set credentials (HiveMQ Cloud) in `.env`:

```bash
# edit .env and set:
# HIVEMQ_USERNAME=...
# HIVEMQ_PASSWORD=...
```

2. Run the simulator (publishes retained status to MQTT):

```bash
python -m simulated_city --steps 200
```

3. Run the dashboard and select **MQTT** in the sidebar:

```bash
streamlit run scripts/dashboard/bin_dashboard.py
```


## Coding constraints

- Follow the guidelines in [copilot-instructions.md](copilot-instructions.md).
- Keep the code readable and easy to extend.
- Support more than one location.

## Realism improvements (ideas)

If you want the simulation to feel more like real life, the highest-value additions are:

- **Time-of-day patterns**: arrival probability varies by hour/day (weekday vs weekend).
- **Bag size distribution**: use a distribution (e.g., small/medium/large) instead of constant `+2%`.
- **Different locations behave differently**: residential vs commercial areas, events, seasonality.
- **Overflow behavior**: if all bins are full, model littering/illegal dumping or people walking to another location.
- **Sensor realism**: noisy measurements, delayed reporting, missing MQTT messages.
- **Container capacity differences**: per-container size, compaction, or different waste fractions.

Later (when emptying is in scope):

- **Collection schedules** (fixed days/times) or **threshold-based dispatch**.
- **Truck routing** between multiple locations using real distances (geo transforms already exist in `src/simulated_city/geo.py`).
 