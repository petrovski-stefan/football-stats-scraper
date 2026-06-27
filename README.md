# Leagues Teams Summarizer

A web scraper that collects football match data across multiple leagues — including match results, odds, team positions, and half-time scores — and exports everything to structured CSV files for analysis.

## What it does

1. Reads a list of league URLs from `config/LEAGUES.txt`
2. Navigates each league page using a headless Chrome browser
3. Discovers all stages (regular season, groups, etc.) and rounds within each league
4. Scrapes every match in every round, collecting:
   - Team names and their current league positions
   - Full-time and half-time goals
   - Betting odds (home win / draw / away win)
   - Stage, round, date, and match position in the round
5. Validates data with Pydantic and saves per-league CSV files to `data/`

## Tech stack

| Tool | Purpose |
|---|---|
| Selenium | Headless Chrome browser automation |
| BeautifulSoup4 | HTML parsing |
| Pandas | CSV output |
| Pydantic | Match data validation |
| ThreadPoolExecutor | Concurrent match processing (5 workers) |
| `uv` | Dependency management |

## Project structure

```
.
├── config/
│   └── LEAGUES.txt       # One league URL per line
├── data/                 # Output CSVs (one per league)
├── main.py               # Entry point
├── ids.py                # Discovers match IDs from a league page
├── match.py              # Pydantic model for a single match
├── parsers.py            # HTML -> match dict parsing
├── driver.py             # Selenium Chrome driver setup
├── df.py                 # Pandas CSV save logic
├── links.py              # Reads LEAGUES.txt
└── constants.py          # User agents, stage keywords, column order
```

## Setup

Requires Python 3.13+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

Chrome must be installed — the scraper runs it in headless mode.

## Usage

Add league URLs (one per line) to `config/LEAGUES.txt`, then run:

```bash
uv run python main.py
```

Output CSVs will be written to `data/<league_name>.csv`.

## Output columns

| Column | Description |
|---|---|
| `league_name` | League identifier |
| `year` / `period` / `stage` / `round` | Match context |
| `date` | Match date |
| `first_team_name` / `second_team_name` | Home and away teams |
| `first_team_position` / `second_team_position` | League table positions |
| `home_team_win_initial_odds` / `draw_initial_odds` / `away_team_win_initial_odds` | Opening betting odds |
| `has_odds` | Whether all three odds were available |
| `first_team_final_goals` / `second_team_final_goals` | Full-time score |
| `first_team_first_half_goals` / `second_team_first_half_goals` | Half-time score |
| `is_match_7plus` | True if the match had 7 or more total goals |
| `is_match_transition` | True if the losing team at half-time won the match |
| `is_first_match_in_round` / `is_last_match_in_round` | Match position within its round |

## Notes

- User agents are rotated randomly per request to reduce bot detection.
- Portuguese special characters in team/league names are transliterated to ASCII before being used as file names.
- If a CSV for the league already exists, it is overwritten with the new data.
