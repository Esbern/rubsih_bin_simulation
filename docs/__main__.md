# CLI entrypoint (`simulated_city.__main__`)

This template includes a tiny CLI smoke test.

It does **not** run a simulation. It only verifies that configuration loading works and prints the MQTT broker settings.


## Run

From the repo root:

```bash
python -m simulated_city
```

Expected output includes:

- broker host/port and whether TLS is enabled
- base topic


## Function

### `main() -> None`

Example (calling directly):

```python
from simulated_city.__main__ import main

main()
```
