# Setup

This project targets **Python 3.11**.
This project targets **Python 3.11+**.

## Create and activate a virtual environment

macOS / Linux:

```bash
 python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

Windows (PowerShell):

```powershell
 py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

## Install the library (editable) + workshop tools

```bash
pip install -e ".[dev,notebooks]"
```

## Optional: geospatial transforms (CRS)

If you plan to work with real-world coordinates, install the optional geospatial
extra to enable EPSG transforms.

Geo helpers live in `simulated_city.geo` and include convenience functions like
`wgs2utm(...)` / `utm2wgs(...)` plus the general `transform_xy(...)`.

```bash
pip install -e ".[geo]"
```

Tip: for notebooks that include both mapping + CRS transforms, you can install both extras:

```bash
pip install -e ".[notebooks,geo]"
```

## Run notebooks

- VS Code: open a notebook in `notebooks/` and select the `.venv` kernel.
- Or start Jupyter:

```bash
jupyter lab
```

## Run tests

```bash
python -m pytest
```
