# Get-CWFIS-Lightning

A complete pipeline to extract Canadian Lightning Detection Network (CLDN) strike data from PostgreSQL, bin strikes by time windows, and generate publication-ready maps of Canada with provincial/territorial boundaries.

**Status:** ✅ Production Ready

## Overview

This project:
1. **Queries** the CLDN database (PostgreSQL on s-edm-genii) for lightning strikes from the past N hours
2. **Bins** strikes into exclusive time windows (1h, 6h, 12h, 24h, 48h)
3. **Maps** strikes on a professional map of Canada with:
   - All provinces and territories outlined
   - Light grey land masses, light blue oceans
   - Strikes color-coded by recency (red=1h, orange=6h, yellow=12h, green=24h)
   - EPSG:3978 projection (Canada Albers Equal Area Conic)

Exports: Raw CSV, binned CSV, and static PNG map.

## Requirements

- **OS:** Windows 11 with PowerShell
- **Python:** 3.11+ (conda base or .venv)
- **VPN:** Active connection to NRCan network (access s-edm-genii:5432)
- **Database:** Read access to `cwfis.bt.cldn_strikes` table

## Installation

### 1. Setup Virtual Environment
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
TABLE=<table-name>
PASSWORD=<database-password>
```

**Required Fields:**
- `HOST`: PostgreSQL server hostname (e.g., `s-edm-genii`)
- `USER`: Database username (e.g., `fire`)
- `DATABASE`: Database name (e.g., `cwfis`)
- `TABLE`: Lightning strikes table name (e.g., `bt.cldn_strikes`)
- `PASSWORD`: Database password for authentication

**Security:** 
- Keep `.env` out of version control (add to `.gitignore`)
- Do NOT commit actual credentials to GitHub
- Use strong passwords
- Ensure .env file has restricted permissions (readable only by user)

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
- **Location:** `tmp/CLDN_export_24h_<timestamp>.csv`
- **Format:** 22 columns (cld_id, rep_date, lon, lat, peak_current, etc.)
- **Rows:** ~98K-100K per 24h window

### Binned CSV Export
- **Location:** `tmp/CLDN_binned_24h_<timestamp>.csv`
- **Columns:** cld_id, rep_date, lon, lat, peak_current, num_sensor, **time_bin**, hours_elapsed
- **Bins:** Exclusive (no overlap) time windows:
  - `bin_1h`: Past 1 hour
  - `bin_6h`: 1–6 hours ago
  - `bin_12h`: 6–12 hours ago
  - `bin_24h`: 12–24 hours ago
  - `bin_48h`: 24–48 hours ago
  - `bin_older`: 48+ hours ago

### Map PNG
- **Location:** `images/CLDN_strikes_24h_<timestamp>.png`
- **Resolution:** 150 DPI
- **Size:** ~16"×12" (3000×2400 pixels approx.)
- **Features:**
  - 4,596 admin boundaries (provinces, territories, states)
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
├── SCHEMA.txt                    (Database table schema reference)
├── main.py                       (CLI entry point)
├── src/
│   ├── __init__.py
│   ├── config.py                 (Load .env credentials)
│   ├── db_connector.py           (PostgreSQL queries & CSV export)
│   ├── binning.py                (Temporal binning logic)
│   ├── mapper.py                 (Geospatial visualization)
│   └── provinces_data.py         (Provincial boundary download/fallback)
├── tmp/                          (Temporary data - CSV exports)
│   └── CLDN_export_*.csv
│   └── CLDN_binned_*.csv
└── images/                       (Output maps)
    └── CLDN_strikes_*.png
```

## Pipeline Phases

### Phase 1: Database Query
- Connect to PostgreSQL (s-edm-genii:5432)
- Query `cwfis.bt.cldn_strikes` for past N hours
- Export to CSV with all 22 columns

### Phase 2: Temporal Binning
- Load CSV and parse timestamps (rep_date column)
- Assign each strike to exclusive time bin
- Export binned CSV with `time_bin` column

### Phase 3: Geospatial Visualization
- Load Natural Earth admin level 1 boundaries (4,596 features)
- Project to Canada Albers (EPSG:3978)
- Plot land masses (light grey), boundaries (black), ocean (light blue)
- Scatter plot strikes with time bin colors
- Add legend, title, grid, annotation
- Export PNG at 150 DPI

## Data Sources

| Component | Source | Format | Notes |
|-----------|--------|--------|-------|
| Lightning Strikes | PostgreSQL cwfis.bt.cldn_strikes | 22 columns, UTC timestamps | NRCan internal |
| Admin Boundaries | Natural Earth (GitHub mirror) | GeoJSON 10m resolution | 4,596 features (all N. America) |
| Projection | EPSG:3978 | Canada Albers | Suitable for Canada mapping |

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

Install all at once:
```bash
pip install -r requirements.txt
```

## Database Schema

Key columns in `cwfis.bt.cldn_strikes`:

| Column | Type | Purpose |
|--------|------|---------|
| cld_id | INTEGER | Primary key |
| rep_date | TIMESTAMP | **Time column for binning** |
| lon | DOUBLE PRECISION | Longitude (WGS84) |
| lat | DOUBLE PRECISION | Latitude (WGS84) |
| peak_current | INTEGER | Strike magnitude (mA) |
| num_sensor | INTEGER | Number of sensors detecting strike |
| cg | INTEGER | Cloud-to-ground indicator |
| the_geom | USER-DEFINED | Geometry column |
| *16 others* | Various | Timing, quality, location metrics |

See [SCHEMA.txt](SCHEMA.txt) for complete list.

## Troubleshooting

### Connection Fails
- **Error:** `ConnectionResetError` or `could not connect to server`
- **Solution:** 
  1. Check VPN is active
  2. Verify credentials in `.env`
  3. Test: `ping 192.139.6.65`

### Module Not Found
- **Error:** `ModuleNotFoundError: No module named 'psycopg2'`
- **Solution:** 
  ```bash
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### No Provinces Plotting
- **Error:** Map shows no boundaries
- **Solution:** Script falls back to embedded province data if GitHub unavailable
- Check internet connection or try later

### Map Takes Long Time
- **Why:** 4,596 boundaries need explicit line drawing for black outlines
- **Duration:** 30–45 seconds typical for 98K strikes + boundaries

## Performance Notes

- **Query time:** 5–15 seconds (98K strikes)
- **Binning time:** 2–3 seconds
- **Map generation:** 30–45 seconds (includes boundary download if needed)
- **Total:** ~1 minute per run

## Future Enhancements

- [ ] Support other output formats (GeoTIFF, interactive HTML)
- [ ] Batch processing (multiple time windows)
- [ ] Real-time dashboard
- [ ] Strike intensity heatmap
- [ ] PDF export
- [ ] Linux/macOS compatibility

## References

- **CLDN Database:** `s-edm-genii` (NRCan internal)
- **Natural Earth:** https://www.naturalearthdata.com/
- **EPSG:3978:** Canada Albers Equal Area Conic
- **GeoPandas Docs:** https://geopandas.org/

## License

Internal use - NRCan