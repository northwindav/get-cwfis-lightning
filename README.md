# Get-CWFIS-Lightning

_This code was written with the assistance of AI agents, but has been reviewed by a human_

A complete pipeline to extract Canadian Lightning Detection Network (CLDN) strike data from PostgreSQL, bin strikes by time windows, and generate publication-ready maps of Canada with provincial/territorial boundaries.

## Overview

This project:
1. Queries the CWFIS CLDN database (PostgreSQL on s-edm-genii) for lightning strikes from the past N hours
2. Bins strikes into exclusive time windows (1h, 6h, 12h, 24h, 48h)
3. MPlots all strikes on an EPSG3978 map of Canada including:
   - All provinces and territories outlined
   - Strikes color-coded by recency (red=1h, orange=6h, yellow=12h, green=24h)

Exports: Raw CSV, binned CSV, and static PNG map.

## Requirements

- **OS:** Windows 11 with PowerShell
- **Python:** 3.11+ (conda base or .venv)
- **Network:** A connection to the NoFC server, either directly or via VPN
- **Database:** Read access to the CWFIS database. See below for required contents of the .env file

## Installation

### 1. Setup Virtual Environment and activate
```bash
cd get-cwfis-lightning
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Credentials
Create `.env` file in the project root with the following required fields:

```env
HOST=<database-server-hostname>
USER=<database-username>
DATABASE=<database-name>
TABLE=<lightning-table-name>
PASSWORD=<database-password>
```

## Usage

### Basic (24 hours)
```bash
.\.venv\Scripts\Activate.ps1
python main.py
```

### Custom Time Range
```bash
python main.py --hours 12          # 12h data
python main.py --hours 48          # 48h data
python main.py --hours 72          # 72h data
```

### Verbose Logging
```bash
python main.py --hours 24 -v
```

### Custom Output Directory
```bash
python main.py --hours 24 --output-dir c:\custom\path
```

## Output Files

All outputs are timestamped with ISO UTC format.

### Raw CSV Export
- **Location:** `tmp/CLDN_export_<# hours back>_<timestamp>.csv`
- **Format:** csv with all available columns

### Binned CSV Export
- **Location:** `tmp/CLDN_binned_<# hours back>_<timestamp>.csv`
- **Bins:** Exclusive (no overlap) time windows:
  - `bin_1h`: Past 1 hour
  - `bin_6h`: 1–6 hours ago
  - `bin_12h`: 6–12 hours ago
  - `bin_24h`: 12–24 hours ago
  - `bin_48h`: 24–48 hours ago
  - `bin_older`: 48+ hours ago

### Map PNG
- **Location:** `images/CLDN_strikes_<# hours back>_<timestamp>.png`
- **Admin info:**
  - Juridictional boundaries
  - Strike scatter plot with legend
  - Time bin color codes
  - Grid, title, projection info

**Color Scheme (by time bin):**
- 🔴 Red (#FF0000): Past 1h
- 🟠 Orange (#FF8800): 1–6h ago
- 🟡 Yellow (#FFDD00): 6–12h ago
- 🟢 Green (#00AA00): 12–24h ago
- 🔵 Blue (#0000FF): 24–48h ago
- ⚫ Gray (#666666): 48h+ ago

## Project Structure

```
get-cwfis-lightning/
├── .env                          (Credentials - NOT in git)
├── .venv/                        (Python virtual environment)
├── requirements.txt              (Dependencies)
├── README.md                     (This file)
├── main.py                       (CLI entry point)
├── src/
│   ├── __init__.py
│   ├── config.py                 (Load .env credentials)
│   ├── db_connector.py           (PostgreSQL queries & CSV export)
│   ├── binning.py                (Temporal binning logic)
│   ├── mapper.py                 (main plotting script)
│   └── provinces_data.py         (Provincial boundary download including a fallback)
├── tmp/                          (Temporary data - CSV exports)
│   └── CLDN_export_*.csv
│   └── CLDN_binned_*.csv
└── images/                       (Output maps)
    └── CLDN_strikes_*.png
```

## Under the hood: What happens when main.py is called

### Step 1: Database Query
- Connect to PostgreSQL (s-edm-genii:5432)
- Query `cwfis.bt.cldn_strikes` for past N hours
- Export to CSV with all 22 columns

### Step 2 2: Temporal Binning
- Load CSV and parse timestamps (rep_date column)
- Assign each strike to exclusive time bin
- Export binned CSV with `time_bin` column

### Step 3: Map creation
- Load Natural Earth admin level 1 boundaries
- Project to Canada Albers (EPSG:3978)
- Plot land masses (light grey), boundaries (black), ocean (light blue)
- Scatter plot strikes with time bin colors
- Add legend, title, grid, annotation
- Export PNG at 150 DPI

## Data Sources

| Component | Source | Format | Notes |
|-----------|--------|--------|-------|
| Lightning Strikes | PostgreSQL cwfis.bt.cldn_strikes | 22 columns, UTC timestamps | NRCan internal |
| Admin Boundaries | Natural Earth | GeoJSON 10m resolution | all of North America |
| Projection | EPSG:3978 | Canada Albers |  |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| psycopg2-binary | ≥2.9.0 | PostgreSQL adapter |
| pandas | ≥2.0.0 | Data manipulation |
| geopandas | ≥1.0.0 | Geospatial operations |
| shapely | ≥2.0.0 | Geometric shapes |
| matplotlib | ≥3.8.0 | Map visualization |
| fiona | ≥1.10.0 | Vector I/O |
| pyogrio | ≥0.8.0 | GIS I/O |
| python-dotenv | ≥1.0.0 | .env loading |
| requests | ≥2.31.0 | HTTP requests |

## License

Internal use - NRCan