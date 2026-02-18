# Exercises

This repository started as a workshop template. The simulation code is intentionally small and readable so you can extend it.

## Rubbish-bin filling simulation

### What it does

- Simulates one or more locations in Copenhagen (lat/lon)
- Each location has three containers: `left`, `center`, `right`
- Each timestep, a person may arrive and deposit a bag
- Publishes retained MQTT status messages when container fill crosses a boundary (e.g. every 10%)

### Configure it

Edit `config.yaml` and set `simulation.locations`.

Example:

```yaml
simulation:
  timestep_minutes: 15
  arrival_prob: 0.25
  bag_fill_delta_pct: 2
  status_boundary_pct: 10

  # Optional: fixed simulation start time (UTC) for deterministic plots/logs
  # start_time: "2026-02-18T00:00:00Z"
  # Optional: delay between timesteps (MQTT/dashboard testing)
  # step_delay_s: 0.25
  # seed: 123
  locations:
    - id: "city_hall"
      lat: 55.67597
      lon: 12.56984
```

### Run it

Dry-run (no MQTT publish):

```bash
python -m simulated_city --steps 200 --dry-run
```

In dry-run mode the simulation prints the MQTT `topic=...` and `payload=...` it
would have published. If you run a small number of steps you might see no output
until a container crosses the first boundary (by default 10%).

If you want more frequent events (better for dashboards), set
`simulation.publish_every_deposit: true` in `config.yaml`.

If you add `--log-file sim_status.jsonl`, the simulator writes JSONL events to
that file and **overwrites it per run**.

Publish MQTT status messages:

```bash
python -m simulated_city --steps 200
```

### Extension ideas

- Add an "unable to deposit" event when all containers are full.
- Vary arrivals by time-of-day.
- Use a bag size distribution instead of a fixed `bag_fill_delta_pct`.
- Add emptying/collection once filling is solid and tested.
