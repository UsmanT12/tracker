# WNBA Stats Tracker

A Python project that collects player box-score statistics from the official
WNBA website, stores them in PostgreSQL, and displays the data with Matplotlib
charts.

## Pipeline

1. Selenium loads the WNBA schedule and collects each game's box-score URL.
2. The box-score scraper extracts statistics for the players listed in
   `load_database/players.py`.
3. The statistics are inserted or updated in the PostgreSQL `player_stats`
   table.
4. The chart program queries PostgreSQL and displays player statistics,
   calendar heatmaps, and field-goal analysis.

## Setup

Create or activate a Python environment and install the required packages:

```bash
pip install selenium psycopg2-binary matplotlib numpy pandas
```

Make sure PostgreSQL is running and that the `player_stats` table already
exists. Update `config.py` with:

- The path to ChromeDriver
- The WNBA schedule URL and season
- Your PostgreSQL host, database, username, password, and port

## Run the web scraper

From the project root:

```bash
python load_database/main.py
```

The scraper opens the configured WNBA schedule, visits every box score, and
upserts the selected players' statistics into PostgreSQL.

## Run the charts

From the project root:

```bash
python main.py
```

Choose an option from the terminal menu to:

- View all stored player statistics
- Display a player's points calendar
- Display a player's field-goal percentage calendar
- Display a player's field goals made and attempted
- Analyze field-goal efficiency
