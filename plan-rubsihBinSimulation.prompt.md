## Plan: README Cleanup + Realism Roadmap (DRAFT)

Update the project README so it clearly and correctly describes your intended simulation: 3 containers per location, 15-minute timesteps, stochastic arrivals, and fill modeled in percent. Then add a short “realism roadmap” section listing extra features that would make it closer to real life, without implementing them yet. While doing this, fix a couple of repo/documentation mismatches (README filename vs pyproject, and MQTT env var names) so the docs don’t contradict the code.

**Steps**
1. Restructure the README content
   - Convert `RERADME.md` into a proper README with a top-level title and sections: Goal, Simulation Rules, MQTT Outputs, Current Status/Scope, Next Ideas.
   - Correct spelling/grammar and clarify ambiguous statements (e.g., waste vs waist, container names, “if full then fallback” behavior).
2. Clarify the simulation spec in the README (based on your answers)
   - Define state variables per container: `fill_pct` in 0–100, plus “full” at 100%.
   - Define timestep: 15 minutes.
   - Define arrivals: 25% chance per timestep of a person arriving (and depositing 2% if that’s the intended increment; otherwise specify the bag size in % explicitly).
   - Define bin-choice: 50% Center, 25% Left, 25% Right; if chosen is full, pick another non-full (define tie-breaking).
3. Document MQTT publishing behavior (no new code yet)
   - Add a “MQTT messages” section describing what you want: publish a status update whenever fill crosses each 10% boundary (“status for each 10 pct”), including payload fields and a proposed topic format.
   - Point to existing MQTT helper plumbing in `src/simulated_city/mqtt.py` as the intended transport layer.
4. Fix naming and doc consistency issues so the repo reads cleanly
   - Align `pyproject.toml` `readme = "README.md"` with the actual README file you keep (either rename the file to README.md or change pyproject).
   - Align MQTT env var naming between `install-readme.md`, `config.yaml`, and `.env.example` (currently inconsistent).
   - (Optional but high-value) Add a minimal placeholder for the missing `docs/exercises.md` referenced by `docs/overview.md` and `src/simulated_city/__main__.py`, or remove those references to avoid dead links.
5. Add “Realism Improvements” section (ideas only, mapped to likely future modules)
   - Variable arrival rates (time-of-day/weekday seasonality).
   - Bag size distribution (not constant) and deposit failures/overflow behavior.
   - Multiple locations (you already want this) with lat/lon, and per-location demand differences.
   - Container-specific constraints (different capacities, contamination/incorrect sorting).
   - Sensor noise and delayed reporting (makes MQTT/dashboard more realistic).
   - Missed deposits/littering events when all bins are full.
   - (Later) Emptying/truck collection strategies once in scope (scheduled vs threshold-based vs route planning), leveraging `src/simulated_city/geo.py` for distance/time.

**Verification**
- Run markdown lint (if you use one) to ensure a proper H1 and no trailing whitespace.
- Run existing tests to ensure doc-only changes didn’t break anything: `pytest`.
- Quick manual check: README instructions match `config.yaml` and env var names.

**Decisions**
- Fill unit: percent (0–100%).
- Timestep: 15 minutes.
- Emptying: explicitly out of scope for now.
- MQTT: publish status updates at each 10% fill boundary (documented as the target behavior).
