## Plan: Streamlit Bin Dashboard (MQTT + Replay)

The repo already has the core simulation publishing retained MQTT status messages on `{base_topic}/bins/{location_id}/{container}/status`, and there’s a draft Streamlit dashboard in [scripts/dashboard/bin_dashboard.py](scripts/dashboard/bin_dashboard.py) that reads MQTT or tails a JSONL log. Based on your answers, the remaining work is to (1) change log-file support from “tail” to true “replay”, (2) ensure bins appear immediately at 0% (even before any status events are emitted), while keeping the UI minimal: one line chart (last 24h), and a single alert banner + list for bins ≥ 80%, with timestamp on the x-axis.

**Steps**
1. Confirm/lock the message contract used by the dashboard  
   - Use `make_status_payload` in [src/simulated_city/rubbish_sim.py](src/simulated_city/rubbish_sim.py) as the single source of truth for fields (`ts`, `location_id`, `container`, `fill_pct`, etc.).  
   - Ensure the JSONL log format stays `{"topic": "...", "payload": {...}}` as written by `JsonlFileStatusPublisher`.

2. Make bins visible immediately at 0% in both MQTT + log modes  
   - Preferred (most correct for MQTT): publish an initial retained status for each `{location_id}×{left,center,right}` at simulation start in `run_simulation` in [src/simulated_city/rubbish_sim.py](src/simulated_city/rubbish_sim.py), with `fill_pct=0` and a distinct `event` value (e.g., `init`) so consumers can distinguish it.  
   - Ensure the same initial statuses are also written to JSONL when `--log-file` is used (so replay starts with visible lines).

3. Implement true “Replay file” semantics in the Streamlit dashboard  
   - Extend [scripts/dashboard/bin_dashboard.py](scripts/dashboard/bin_dashboard.py) to support two log modes: “Tail live file” (keep as-is, even if not the default) and “Replay file” (your selected requirement).  
   - For replay: read and parse the entire JSONL file into a list of `StatusEvent` sorted by `ts`. Maintain replay state in `st.session_state` (`replay_started_at_wallclock`, `replay_started_at_event_ts`, `replay_idx`, `speed_multiplier`, `playing`).  
   - On each refresh, compute the “virtual replay time” and append all events with `event.ts <= virtual_time` into the dataframe backing the chart.

4. Keep the UI exactly to spec (minimal)  
   - Main area: a single `st.line_chart` of `fill_pct` over time (pivoted by `{location_id}.{container}`), filtered to last 24h.  
   - Alert: one banner (error) if any active alerts, plus a small list/table of the affected series + latest `fill_pct`.  
   - Sidebar: source selection (MQTT vs Log), refresh interval, play/pause + speed control for replay, and alert threshold (default 80).

5. Reduce duplication by reusing existing MQTT utilities  
   - Refactor dashboard MQTT connection to use `connect_mqtt` and topic helpers in [src/simulated_city/mqtt.py](src/simulated_city/mqtt.py) rather than hand-rolling the paho client (keeps TLS/credentials consistent with [src/simulated_city/config.py](src/simulated_city/config.py)).

6. Documentation touch-up for running the dashboard  
   - Add a short “Dashboard” section to either [README.md](README.md) or [docs/demos.md](docs/demos.md) with: `python -m pip install -e ".[dashboard]"`, how to run Streamlit from repo root, and example commands to generate MQTT or a replayable log (`python -m simulated_city --steps ... --log-file ...`).

**Verification**
- Unit tests: `python -m pytest -q`
- Manual (log replay):  
  - `python -m simulated_city --steps 200 --dry-run --log-file sim_status.jsonl`  
  - `streamlit run scripts/dashboard/bin_dashboard.py`  
  - Confirm: bins appear immediately at 0%, replay advances over time, alert triggers at ≥ 80%, chart shows last 24h.
- Manual (MQTT live):  
  - Start dashboard (MQTT source) and run simulator without `--dry-run`; confirm retained initial statuses arrive on connect and chart/alerts update.

**Decisions**
- Chose simulator-side initial retained publish to guarantee “show immediately (0%)” for MQTT without dashboard hacks.
- Chose timestamp (`ts`) as the single x-axis for both MQTT and replay modes, per your preference.
