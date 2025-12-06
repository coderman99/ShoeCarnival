# ShoeCarnival Data Tracker

This repository stores lightweight CSV datasets to track:

- Annual Zoom user counts.
- Shoe Station store locations.
- Shoe Carnival store locations.
- Annual sales performance for high-end shoes.

## Data files

- `data/zoom_users.csv`: Annual average monthly Zoom users (millions) with context notes.
- `data/shoe_station_locations.csv`: Store-level information for Shoe Station locations, including city, state, address, and format.
- `data/shoe_carnival_locations.csv`: Store-level information for Shoe Carnival locations with the same schema.
- `data/high_end_shoe_sales.csv`: Annual revenue (USD millions) for key high-end shoe categories with explanatory notes.

Each CSV includes headers for easier import into spreadsheets or analytics tools.

## Fetching updated data

Use the `scripts/fetch_data.py` helper to download fresh inputs for sales and margin projections. Data source endpoints and outputs are controlled through `config/data_sources.yml`, which supports environment variable substitution (e.g., `${ZOOM_USERS_URL}`).

```bash
# Install dependencies
pip install -r requirements.txt

# Fetch all sources defined in the config
python scripts/fetch_data.py

# Fetch a single source and overwrite existing files
HIGH_END_SHOE_SALES_URL="https://example.com/high_end_sales.csv" \
python scripts/fetch_data.py --source high_end_shoe_sales --force
```

If no HTTP URL is provided for a source, the script copies the fallback CSV already checked into this repository so downstream analysis can still proceed.
